from io import BytesIO


def test_family_profiles_are_owner_scoped(client, patient_headers):
    created = client.post("/api/family", json={"name": "Riya Sharma", "relationship": "Child", "date_of_birth": "2018-06-12", "medical_info": "Family-shared notes"}, headers=patient_headers)
    assert created.status_code == 201
    member_id = created.json["member"]["id"]
    assert client.get("/api/family", headers=patient_headers).json["members"][0]["name"] == "Riya Sharma"
    other = client.post("/api/auth/register", json={"name": "Other Patient", "email": "family-other@example.test", "password": "AnotherPass123", "role": "patient"}).json
    other_headers = {"Authorization": f"Bearer {other['token']}"}
    assert client.put(f"/api/family/{member_id}", json={"name": "Changed", "relationship": "Child"}, headers=other_headers).status_code == 404
    assert client.delete(f"/api/family/{member_id}", headers=other_headers).status_code == 404
    assert client.put(f"/api/family/{member_id}", json={"name": "Riya Sharma", "relationship": "Daughter", "medical_info": "Updated"}, headers=patient_headers).status_code == 200


def test_medicine_sources_and_taken_history(client, patient_headers, doctor_headers):
    patient = client.get("/api/auth/me", headers=patient_headers).json["user"]
    doctor = client.get("/api/auth/me", headers=doctor_headers).json["user"]
    family = client.post("/api/family", json={"name": "Kabir Sharma", "relationship": "Child"}, headers=patient_headers).json["member"]
    patient_entry = client.post("/api/medicines", json={"name": "Demo record", "dosage": "As directed by clinician", "frequency": "As recorded", "start_date": "2026-10-18", "reminder_times": "08:00", "family_member_id": family["id"]}, headers=patient_headers)
    assert patient_entry.status_code == 201
    prescription = client.post("/api/medicines/prescriptions", json={"patient_id": patient["id"], "name": "Clinician record", "dosage": "Clinician-entered", "frequency": "Clinician-entered", "start_date": "2026-10-18"}, headers=doctor_headers)
    assert prescription.status_code == 201
    medicines = client.get("/api/medicines", headers=patient_headers).json["medicines"]
    assert {item["source"] for item in medicines} == {"patient-entered", "doctor-prescribed"}
    taken = client.post(f"/api/medicines/{patient_entry.json['id']}/taken", headers=patient_headers)
    assert taken.status_code == 201
    assert client.get(f"/api/medicines?patient_id={patient['id']}", headers=doctor_headers).status_code == 200
    assert doctor["role"] == "doctor"


def test_private_report_upload_and_access_control(client, app, patient_headers):
    invalid = client.post("/api/reports/uploads", data={"title": "Invalid file", "category": "lab", "file": (BytesIO(b"not really a pdf"), "report.pdf", "application/pdf")}, headers=patient_headers, content_type="multipart/form-data")
    assert invalid.status_code == 400
    uploaded = client.post("/api/reports/uploads", data={"title": "Demo lab report", "category": "lab", "file": (BytesIO(b"%PDF-1.4 demo"), "lab.pdf", "application/pdf")}, headers=patient_headers, content_type="multipart/form-data")
    assert uploaded.status_code == 201
    report_id = uploaded.json["upload"]["id"]
    headers = {"Authorization": f"Bearer {client.post('/api/auth/register', json={'name': 'Another Patient', 'email': 'upload-other@example.test', 'password': 'AnotherPass123', 'role': 'patient'}).json['token']}"}
    assert client.get(f"/api/reports/uploads/{report_id}/file", headers=patient_headers).data == b"%PDF-1.4 demo"
    assert client.get(f"/api/reports/uploads/{report_id}/file", headers=headers).status_code == 404
    assert len(client.get("/api/reports/uploads", headers=patient_headers).json["uploads"]) == 1
    assert not (app.config["DATABASE_PATH"].parent / "public").exists()


def test_demo_bed_booking_reference_history_and_cancel(client, patient_headers):
    hospital = client.get("/api/hospitals").json["hospitals"][0]
    family = client.post("/api/family", json={"name": "Family Patient", "relationship": "Parent"}, headers=patient_headers).json["member"]
    response = client.post("/api/hospitals/bookings", json={"hospital_id": hospital["id"], "bed_type": "General ward", "patient_name": family["name"], "family_member_id": family["id"], "admission_date": "2026-11-03"}, headers=patient_headers)
    assert response.status_code == 201
    booking = response.json["booking"]
    assert booking["reference"].startswith("MB-")
    assert booking["status"] == "pending-demo"
    assert "does not reserve" in booking["message"]
    assert client.get("/api/hospitals/bookings", headers=patient_headers).json["bookings"][0]["reference"] == booking["reference"]
    assert client.patch(f"/api/hospitals/bookings/{booking['reference']}", headers=patient_headers).json["status"] == "cancelled-demo"
