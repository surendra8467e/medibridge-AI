import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app


@pytest.fixture
def app(tmp_path):
    database = tmp_path / "test-medibridge.sqlite"
    return create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret",
        "DATABASE_PATH": database,
        "UPLOAD_DIRECTORY": tmp_path / "private-uploads",
        "CORS_ORIGINS": ["http://localhost:5173"],
    })


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, email, password):
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json['token']}"}


@pytest.fixture
def patient_headers(client):
    return login(client, "patient@medibridge.demo", "DemoPatient123!")


@pytest.fixture
def admin_headers(client):
    response = client.post("/api/admin/login", json={"email": "admin@medibridge.demo", "password": "DemoAdmin123!"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json['token']}"}


@pytest.fixture
def doctor_headers(client, admin_headers):
    doctor = client.post("/api/auth/login", json={"email": "doctor@medibridge.demo", "password": "DemoDoctor123!", "role": "doctor"})
    doctor_id = doctor.json["user"]["id"]
    changed = client.patch(f"/api/admin/doctors/{doctor_id}/verification", json={"status": "verified", "note": "Verified for this isolated test"}, headers=admin_headers)
    assert changed.status_code == 200
    return {"Authorization": f"Bearer {doctor.json['token']}"}
