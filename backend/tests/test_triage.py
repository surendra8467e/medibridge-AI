from services.triage_service import assess_symptoms
import services.ai_service as ai_service


def test_emergency_symptoms_get_immediate_emergency_guidance(client, patient_headers):
    created = client.post("/api/chat/sessions", headers=patient_headers).json["session"]["id"]
    result = client.post(f"/api/chat/sessions/{created}/messages", json={"content": "I have severe chest pain"}, headers=patient_headers)
    assert result.status_code == 200
    assert result.json["reply"]["stage"] == 3
    assert "112" in result.json["reply"]["response"]
    assert result.json["reply"]["mode"] == "rule-based demo"


def test_three_triage_stages():
    assert assess_symptoms("mild headache")['stage'] == 1
    assert assess_symptoms("very high blood pressure")['stage'] == 2
    assert assess_symptoms("difficulty breathing")['stage'] == 3


def test_configured_ai_cannot_lower_local_urgency(monkeypatch):
    monkeypatch.setenv("AI_API_KEY", "test-key")
    monkeypatch.setattr(ai_service, "_configured_stage", lambda _message, _history=None: 1)
    result = ai_service.respond_to_health_message("very high blood pressure")
    assert result["stage"] == 2
    assert result["mode"] == "configured AI triage"


def test_configured_ai_classifier_receives_recent_conversation_context(monkeypatch):
    monkeypatch.setenv("AI_API_KEY", "test-key")
    observed = {}
    def classifier(message, history):
        observed["message"] = message
        observed["history"] = history
        return 1
    monkeypatch.setattr(ai_service, "_configured_stage", classifier)
    history = [{"sender": "patient", "content": "I have felt unwell for two days"}, {"sender": "assistant", "content": "What symptoms are you experiencing?"}]
    result = ai_service.respond_to_health_message("I have a cough", history=history)
    assert observed["message"] == "I have a cough"
    assert observed["history"] == history
    assert result["mode"] == "configured AI triage"


def test_emergency_bypasses_external_ai(monkeypatch):
    monkeypatch.setenv("AI_API_KEY", "test-key")
    monkeypatch.setattr(ai_service, "_configured_stage", lambda _message, _history=None: (_ for _ in ()).throw(AssertionError("network should not be called")))
    result = ai_service.respond_to_health_message("severe chest pain")
    assert result["stage"] == 3
    assert "112" in result["response"]


def test_vague_symptoms_ask_a_relevant_follow_up(monkeypatch):
    monkeypatch.delenv("AI_API_KEY", raising=False)
    result = ai_service.respond_to_health_message("I have been feeling unwell for two days")
    assert "What symptoms are you experiencing?" in result["response"]
    assert "fever" in result["response"]
    assert result["mode"] == "rule-based demo"


def test_conversation_uses_previous_symptoms_and_does_not_repeat_questions(monkeypatch):
    monkeypatch.delenv("AI_API_KEY", raising=False)
    first = "I have been feeling unwell for two days"
    first_reply = ai_service.respond_to_health_message(first)
    second = "I have fever and headache"
    second_reply = ai_service.respond_to_health_message(second, history=[
        {"sender": "patient", "content": first},
        {"sender": "assistant", "content": first_reply["response"]},
    ])
    assert "temperature" in second_reply["response"].lower()
    assert "stiff neck" in second_reply["response"].lower()
    third = "38.3, no stiff neck or confusion; symptoms are mild but worsening"
    third_reply = ai_service.respond_to_health_message(third, history=[
        {"sender": "patient", "content": first},
        {"sender": "assistant", "content": first_reply["response"]},
        {"sender": "patient", "content": second},
        {"sender": "assistant", "content": second_reply["response"]},
    ])
    assert "From what you've shared" in third_reply["response"]
    assert "38.3" in third_reply["response"]
    assert "temperature" not in third_reply["response"].lower()
    assert "can't determine the cause" in third_reply["response"]


def test_emergency_follow_up_bypasses_questions_and_returns_112_guidance():
    result = ai_service.respond_to_health_message("I now have a stiff neck and confusion")
    assert result["stage"] == 3
    assert "112" in result["response"]
    assert "do not wait" in result["response"].lower()


def test_denied_warning_sign_is_not_misclassified_as_an_emergency():
    assert assess_symptoms("fever and headache, no stiff neck or confusion")['stage'] == 1


def test_chat_api_keeps_multi_turn_symptom_context(client, patient_headers, monkeypatch):
    monkeypatch.delenv("AI_API_KEY", raising=False)
    session_id = client.post("/api/chat/sessions", headers=patient_headers).json["session"]["id"]
    first = client.post(f"/api/chat/sessions/{session_id}/messages", json={"content": "I have been feeling unwell for two days"}, headers=patient_headers).json["reply"]
    assert "What symptoms are you experiencing?" in first["response"]
    second = client.post(f"/api/chat/sessions/{session_id}/messages", json={"content": "I have fever and headache"}, headers=patient_headers).json["reply"]
    assert "temperature" in second["response"].lower()
    third = client.post(f"/api/chat/sessions/{session_id}/messages", json={"content": "38.3, no stiff neck or confusion; symptoms are mild but worsening"}, headers=patient_headers).json["reply"]
    assert "From what you've shared" in third["response"]
    assert "temperature" not in third["response"].lower()
    assert len(client.get(f"/api/chat/sessions/{session_id}/messages", headers=patient_headers).json["messages"]) == 6


def test_chat_api_emergency_overrides_follow_up_stage(client, patient_headers):
    session_id = client.post("/api/chat/sessions", headers=patient_headers).json["session"]["id"]
    client.post(f"/api/chat/sessions/{session_id}/messages", json={"content": "I feel unwell and have a fever"}, headers=patient_headers)
    result = client.post(f"/api/chat/sessions/{session_id}/messages", json={"content": "Now I have a stiff neck and confusion"}, headers=patient_headers).json["reply"]
    assert result["stage"] == 3
    assert "112" in result["response"]


def test_chat_api_mild_headache_asks_specific_questions(client, patient_headers, monkeypatch):
    monkeypatch.delenv("AI_API_KEY", raising=False)
    session_id = client.post("/api/chat/sessions", headers=patient_headers).json["session"]["id"]
    reply = client.post(f"/api/chat/sessions/{session_id}/messages", json={"content": "I have a mild headache since morning."}, headers=patient_headers).json["reply"]
    assert "Where is the pain" in reply["response"]
    assert "blurred vision" in reply["response"]
    assert reply["mode"] == "rule-based demo"


def test_hindi_chat_prefers_hindi_follow_up(client, patient_headers):
    client.patch("/api/auth/language", json={"language": "en"}, headers=patient_headers)
    session_id = client.post("/api/chat/sessions", headers=patient_headers).json["session"]["id"]
    reply = client.post(f"/api/chat/sessions/{session_id}/messages", json={"content": "मुझे सुबह से हल्का सिरदर्द है"}, headers=patient_headers).json["reply"]
    assert "दर्द" in reply["response"]
    assert "धुंधला" in reply["response"]


def test_mild_headache_gets_specific_follow_ups_then_safe_self_care(monkeypatch):
    monkeypatch.delenv("AI_API_KEY", raising=False)
    history = []
    first = "I have a mild headache since morning."
    reply = ai_service.respond_to_health_message(first, history=history)
    assert "Where is the pain" in reply["response"]
    assert "blurred vision" in reply["response"]
    assert "headache since morning" not in reply["response"].lower()
    history.extend([{"sender": "patient", "content": first}, {"sender": "assistant", "content": reply["response"]}])
    second = "Mostly on one side. No fever, vomiting, blurred vision, dizziness, or neck stiffness."
    reply = ai_service.respond_to_health_message(second, history=history)
    assert "gradually" in reply["response"].lower()
    assert "water" in reply["response"].lower() or "sleep" in reply["response"].lower()
    assert "where is the pain" not in reply["response"].lower()
    history.extend([{"sender": "patient", "content": second}, {"sender": "assistant", "content": reply["response"]}])
    third = "It started gradually. I did not drink much water and slept poorly."
    reply = ai_service.respond_to_health_message(third, history=history)
    assert "mild headache since morning" in reply["response"].lower()
    assert "quiet" in reply["response"].lower()
    assert "water" in reply["response"].lower()
    assert "screen" in reply["response"].lower()
    assert "qualified healthcare professional" in reply["response"].lower()
    assert "severe headache" in reply["response"].lower()
    assert reply["mode"] == "rule-based demo"


def test_hindi_headache_input_gets_hindi_follow_up():
    result = ai_service.respond_to_health_message("मुझे सुबह से हल्का सिरदर्द है")
    assert "दर्द" in result["response"]
    assert "दृष्टि" in result["response"] or "बुखार" in result["response"]
    assert result["mode"] == "rule-based demo"


def test_cough_gets_concern_specific_follow_up():
    result = ai_service.respond_to_health_message("I have had a cough since yesterday")
    assert "breathing" in result["response"].lower()
    assert "fever" in result["response"].lower()


def test_chat_history_persists_and_is_private(client, patient_headers):
    session = client.post("/api/chat/sessions", headers=patient_headers).json["session"]["id"]
    client.post(f"/api/chat/sessions/{session}/messages", json={"content": "Mild headache since today"}, headers=patient_headers)
    messages = client.get(f"/api/chat/sessions/{session}/messages", headers=patient_headers).json["messages"]
    assert [message["sender"] for message in messages] == ["patient", "assistant"]
    other = client.post("/api/auth/register", json={"name": "Other", "email": "other@example.test", "password": "AnotherPass123", "role": "patient"}).json
    assert client.get(f"/api/chat/sessions/{session}/messages", headers={"Authorization": f"Bearer {other['token']}"}).status_code == 404
