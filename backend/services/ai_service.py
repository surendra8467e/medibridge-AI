import json
import os
from urllib.request import Request, urlopen
from .triage_service import assess_symptoms, respond_conversationally, _detect_language


def _configured_stage(message, history=None):
    payload = {
        "model": os.getenv("AI_MODEL", "gpt-4o-mini"),
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": "Classify symptom urgency only. Return JSON with integer stage 1 (general), 2 (prompt clinical assessment), or 3 (potential emergency). Consider the full symptom description and warning signs. Do not diagnose or suggest treatment."},
        ] + [{"role": "assistant" if item.get("sender") == "assistant" else "user", "content": item["content"]}
             for item in (history or [])[-8:] if item.get("sender") in ("assistant", "patient")] + [{"role": "user", "content": message}],
    }
    request = Request(os.getenv("AI_API_URL", "https://api.openai.com/v1/chat/completions"),
                      data=json.dumps(payload).encode(),
                      headers={"Authorization": f"Bearer {os.environ['AI_API_KEY']}", "Content-Type": "application/json"},
                      method="POST")
    with urlopen(request, timeout=8) as response:
        result = json.loads(response.read())
    content = json.loads(result["choices"][0]["message"]["content"])
    stage = content.get("stage")
    if type(stage) is not int or stage not in (1, 2, 3):
        raise ValueError("AI response has an invalid triage stage")
    return stage


def respond_to_health_message(message, language="en", history=None):
    history = history or []
    patient_context = " ".join([item["content"] for item in history if item.get("sender") == "patient"] + [message])
    response_language = _detect_language(patient_context, language)
    result = assess_symptoms(patient_context)
    mode = "rule-based demo"
    if result["stage"] != 3 and os.getenv("AI_API_KEY"):
        try:
            result["stage"] = max(result["stage"], _configured_stage(message, history))
            mode = "configured AI triage"
        except Exception:
            mode = "rule-based demo fallback"
    if result["stage"] == 3:
        result["label"] = "Emergency warning"
        result["response"] = ("संभावित आपातकालीन लक्षण हैं। भारत में 112 या अपने स्थानीय आपातकालीन नंबर पर अभी कॉल करें और तुरंत चिकित्सा सहायता लें। ऑनलाइन परामर्श की प्रतीक्षा न करें। यह निदान नहीं है।" if response_language == "hi" else "Potential emergency symptoms were reported. Call 112 in India or your local emergency number now, and seek immediate emergency medical care. Do not wait for an online consultation. This is preliminary guidance, not a diagnosis.")
    elif result["stage"] == 2:
        result["label"] = "Prompt medical assessment"
        result["response"] = ("कृपया योग्य स्वास्थ्य पेशेवर से शीघ्र जांच कराएं। लक्षण गंभीर हों या सीने में दर्द, सांस लेने में कठिनाई, बेहोशी या भ्रम हो तो तुरंत आपातकालीन सहायता लें। इस चैट के आधार पर दवा में बदलाव न करें।" if response_language == "hi" else "Please arrange prompt assessment by a qualified healthcare professional. Seek emergency care immediately if symptoms become severe or you develop chest pain, breathing difficulty, fainting, or confusion. Do not change medication based on this chat.")
    else:
        result["label"] = "General health concern"
        result["response"] = respond_conversationally(message, history, result["stage"], response_language)
    result["mode"] = mode
    result["disclaimer"] = "This is preliminary guidance, not a diagnosis, and does not replace a doctor." if response_language != "hi" else "यह प्रारंभिक मार्गदर्शन है, निदान नहीं और डॉक्टर का विकल्प नहीं है।"
    return result
