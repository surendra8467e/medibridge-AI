from database.db import get_db


def test_health_and_demo_database_initialized(client):
    assert client.get("/api/health").json["status"] == "ok"
    assert client.get("/api/doctors").json["doctors"] == []
    assert client.post("/api/admin/login", json={"email": "admin@medibridge.demo", "password": "DemoAdmin123!"}).status_code == 200


def test_register_login_and_password_hashing(client, app):
    response = client.post("/api/auth/register", json={"name": "New Patient", "email": "new@example.test", "password": "SafePass123!", "role": "patient"})
    assert response.status_code == 201
    with app.app_context():
        stored = get_db().execute("SELECT password_hash FROM users WHERE email=?", ("new@example.test",)).fetchone()["password_hash"]
    assert stored != "SafePass123!"
    assert client.post("/api/auth/login", json={"email": "new@example.test", "password": "SafePass123!"}).status_code == 200


def test_invalid_credentials_and_registration_validation(client):
    assert client.post("/api/auth/login", json={"email": "patient@medibridge.demo", "password": "wrong"}).status_code == 401
    assert client.post("/api/auth/register", json={"email": "bad", "password": "short", "role": "patient"}).status_code == 400


def test_role_restriction_and_patient_privacy(client, patient_headers, doctor_headers):
    assert client.get("/api/doctors/patients/assigned", headers=patient_headers).status_code == 403
    assert client.get("/api/patients/9999", headers=doctor_headers).status_code == 403
    assert client.get("/api/patients/me", headers=doctor_headers).status_code == 403


def test_language_preference_persists(client, patient_headers):
    assert client.patch("/api/auth/language", json={"language": "hi"}, headers=patient_headers).json["language"] == "hi"
    assert client.get("/api/auth/me", headers=patient_headers).json["user"]["language"] == "hi"


def test_role_specific_login_and_unverified_doctor_restrictions(client):
    mismatch = client.post("/api/auth/login", json={"email": "patient@medibridge.demo", "password": "DemoPatient123!", "role": "doctor"})
    assert mismatch.status_code == 403
    registered = client.post("/api/auth/register", json={"name": "Unverified Doctor", "email": "unverified@example.test", "password": "AnotherPass123", "role": "doctor"})
    token = registered.json["token"]
    denied = client.get("/api/doctors/patients/assigned", headers={"Authorization": f"Bearer {token}"})
    assert denied.status_code == 403


def test_demo_doctor_starts_pending_and_can_read_own_profile(client):
    login = client.post("/api/auth/login", json={"email": " DOCTOR@MEDIBRIDGE.DEMO ", "password": "DemoDoctor123!", "role": "doctor"})
    assert login.status_code == 200
    assert login.json["user"]["verificationStatus"] == "pending"
    headers = {"Authorization": f"Bearer {login.json['token']}"}
    profile = client.get("/api/doctors/me", headers=headers)
    assert profile.status_code == 200
    assert profile.json["profile"]["verification_status"] == "pending"
    assert "password" not in profile.json["profile"]
    assert client.get("/api/doctors/patients/assigned", headers=headers).status_code == 403
    assert client.get("/api/appointments", headers=headers).status_code == 403
    assert client.get("/api/doctors").json["doctors"] == []


def test_only_demo_admin_can_change_verification_and_changes_persist(client, patient_headers):
    doctor_login = client.post("/api/auth/login", json={"email": "doctor@medibridge.demo", "password": "DemoDoctor123!", "role": "doctor"})
    doctor_id = doctor_login.json["user"]["id"]
    doctor_headers = {"Authorization": f"Bearer {doctor_login.json['token']}"}
    path = f"/api/admin/doctors/{doctor_id}/verification"
    assert client.get("/api/admin/doctors").status_code == 401
    assert client.get("/api/admin/doctors", headers=patient_headers).status_code == 403
    assert client.patch(path, json={"status": "verified"}, headers=doctor_headers).status_code == 403
    bad_login = client.post("/api/admin/login", json={"email": "admin@medibridge.demo", "password": "wrong"})
    assert bad_login.status_code == 401
    admin_login = client.post("/api/admin/login", json={"email": " ADMIN@MEDIBRIDGE.DEMO ", "password": "DemoAdmin123!"})
    assert admin_login.status_code == 200
    admin_headers = {"Authorization": f"Bearer {admin_login.json['token']}"}
    listing = client.get("/api/admin/doctors", headers=admin_headers)
    assert listing.status_code == 200
    assert listing.json["doctors"][0]["verification_status"] == "pending"
    for status in ("verified", "pending", "rejected"):
        changed = client.patch(path, json={"status": status, "note": f"Demo review: {status}"}, headers=admin_headers)
        assert changed.status_code == 200
        assert client.get("/api/auth/me", headers=doctor_headers).json["user"]["verificationStatus"] == status
    assert client.patch(path, json={"status": "unverified"}, headers=admin_headers).status_code == 400
    events = client.get(f"/api/admin/doctors/{doctor_id}/verification-events", headers=admin_headers)
    assert len(events.json["events"]) == 3


def test_patient_can_sign_in_with_registered_phone(client):
    created = client.post("/api/auth/register", json={"name": "Phone Patient", "email": "phone@example.test", "phone": "+91 98765 43210", "password": "SafePass123!", "role": "patient"})
    assert created.status_code == 201
    login = client.post("/api/auth/login", json={"identifier": "+91 98765 43210", "password": "SafePass123!", "role": "patient"})
    assert login.status_code == 200
    assert login.json["user"]["email"] == "phone@example.test"
