def test_appointment_messages_and_consultation_approval(client, patient_headers, doctor_headers):
    doctor_id = client.get("/api/doctors").json["doctors"][0]["id"]
    created = client.post("/api/appointments", json={"doctor_id": doctor_id, "reason": "General checkup", "scheduled_at": "2026-10-20T10:00"}, headers=patient_headers)
    assert created.status_code == 201
    appointment_id = created.json["appointment"]["id"]
    assert client.patch(f"/api/appointments/{appointment_id}", json={"status": "accepted"}, headers=doctor_headers).status_code == 200
    room = client.get(f"/api/appointments/{appointment_id}/video-room", headers=patient_headers)
    assert room.status_code == 200 and room.json["url"].startswith("https://meet.jit.si/")
    message = client.post(f"/api/patients/{client.get('/api/auth/me', headers=patient_headers).json['user']['id']}/messages", json={"doctor_id": doctor_id, "content": "Thank you"}, headers=patient_headers)
    assert message.status_code == 201
    patient_id = message.json["message"]["patient_id"]
    patient_history = client.get(f"/api/patients/{patient_id}/messages?doctor_id={doctor_id}", headers=patient_headers).json
    doctor_history = client.get(f"/api/patients/{patient_id}/messages", headers=doctor_headers).json
    assert patient_history["conversationId"] == doctor_history["conversationId"] == f"patient-{patient_id}-doctor-{doctor_id}"
    assert len(patient_history["messages"]) == len(doctor_history["messages"]) == 1
    reply = client.post(f"/api/patients/{patient_id}/messages", json={"content": "I received your message"}, headers=doctor_headers)
    assert reply.status_code == 201
    assert len(client.get(f"/api/patients/{patient_id}/messages?doctor_id={doctor_id}", headers=patient_headers).json["messages"]) == 2
    draft = client.post("/api/consultations", json={"appointment_id": appointment_id, "notes": "Patient reports mild concern", "assessment": "Assessment entered by clinician", "advice": "Follow up as needed"}, headers=doctor_headers)
    assert draft.status_code == 201 and draft.json["status"] == "draft"
    assert client.post(f"/api/consultations/{appointment_id}/approve", headers=doctor_headers).status_code == 200
    assert client.post(f"/api/consultations/{appointment_id}/approve", headers=doctor_headers).status_code == 200
    assert len(client.get("/api/reports", headers=patient_headers).json["reports"]) == 1


def test_video_room_requires_accepted_appointment_and_participation(client, patient_headers, doctor_headers):
    doctor_id = client.get("/api/doctors").json["doctors"][0]["id"]
    appointment = client.post("/api/appointments", json={"doctor_id": doctor_id, "reason": "Consultation", "scheduled_at": "2026-10-20T12:00"}, headers=patient_headers).json["appointment"]
    assert client.get(f"/api/appointments/{appointment['id']}/video-room", headers=patient_headers).status_code == 409
    assert client.patch(f"/api/appointments/{appointment['id']}", json={"status": "accepted"}, headers=doctor_headers).status_code == 200
    outsider = client.post("/api/auth/register", json={"name": "Other Patient", "email": "outsider@example.test", "password": "AnotherPass123", "role": "patient"}).json
    denied = client.get(f"/api/appointments/{appointment['id']}/video-room", headers={"Authorization": f"Bearer {outsider['token']}"})
    assert denied.status_code == 403


def test_patient_can_only_cancel_their_own_pending_or_accepted_appointment(client, patient_headers, doctor_headers):
    doctor_id = client.get("/api/doctors").json["doctors"][0]["id"]
    appointment = client.post("/api/appointments", json={"doctor_id": doctor_id, "reason": "Cancel demo", "scheduled_at": "2026-10-22T09:00"}, headers=patient_headers).json["appointment"]
    assert client.post(f"/api/appointments/{appointment['id']}/cancel", headers=doctor_headers).status_code == 403
    assert client.post(f"/api/appointments/{appointment['id']}/cancel", headers=patient_headers).json["status"] == "cancelled"
    assert client.post(f"/api/appointments/{appointment['id']}/cancel", headers=patient_headers).status_code == 404


def test_unassigned_doctor_cannot_read_patient_messages(client):
    doctor_id = client.post("/api/auth/register", json={"name": "Dr Other", "email": "otherdoc@example.test", "password": "AnotherPass123", "role": "doctor"}).json["user"]["id"]
    token = client.post("/api/auth/login", json={"email": "otherdoc@example.test", "password": "AnotherPass123"}).json["token"]
    patient_id = client.post("/api/auth/login", json={"email": "patient@medibridge.demo", "password": "DemoPatient123!"}).json["user"]["id"]
    response = client.get(f"/api/patients/{patient_id}/messages", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_new_patient_messaging_opens_only_after_doctor_accepts(client, doctor_headers):
    registered = client.post("/api/auth/register", json={"name": "Messaging Patient", "email": "messaging-patient@example.test", "password": "AnotherPass123", "role": "patient"})
    patient_headers = {"Authorization": f"Bearer {registered.json['token']}"}
    patient_id = registered.json["user"]["id"]
    doctor_id = client.get("/api/doctors").json["doctors"][0]["id"]
    requested = client.post("/api/appointments", json={"doctor_id": doctor_id, "reason": "Messaging demo", "scheduled_at": "2026-11-04T09:00"}, headers=patient_headers)
    assert requested.status_code == 201
    assert client.get("/api/patients/me/doctors", headers=patient_headers).json["doctors"] == []
    denied = client.post(f"/api/patients/{patient_id}/messages", json={"doctor_id": doctor_id, "content": "Should not send yet"}, headers=patient_headers)
    assert denied.status_code == 403
    appointment_id = requested.json["appointment"]["id"]
    assert client.patch(f"/api/appointments/{appointment_id}", json={"status": "accepted"}, headers=doctor_headers).status_code == 200
    contact = client.get("/api/patients/me/doctors", headers=patient_headers).json["doctors"][0]
    assert contact["id"] == doctor_id
    patient_message = client.post(f"/api/patients/{patient_id}/messages", json={"doctor_id": doctor_id, "content": "Hello, doctor"}, headers=patient_headers).json
    doctor_history = client.get(f"/api/patients/{patient_id}/messages", headers=doctor_headers).json
    assert patient_message["conversationId"] == doctor_history["conversationId"]
    assert doctor_history["appointmentId"] == appointment_id
    assert len(doctor_history["messages"]) == 1
    assert client.post(f"/api/patients/{patient_id}/messages", json={"content": "Hello, patient"}, headers=doctor_headers).status_code == 201
    patient_history = client.get(f"/api/patients/{patient_id}/messages?doctor_id={doctor_id}", headers=patient_headers).json
    assert [message["sender_id"] for message in patient_history["messages"]] == [patient_id, doctor_id]
