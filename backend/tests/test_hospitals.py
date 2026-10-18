def test_demo_hospitals_bed_requests_and_updates(client, patient_headers, doctor_headers):
    hospitals = client.get("/api/hospitals").json["hospitals"]
    assert hospitals and all(hospital["demo"] == 1 for hospital in hospitals)
    hospital_id = hospitals[0]["id"]
    request = client.post(f"/api/hospitals/{hospital_id}/requests", json={"note": "Please contact me"}, headers=patient_headers)
    assert request.status_code == 201
    assert request.json["request"]["status"] == "submitted-demo"
    assert client.patch(f"/api/hospitals/{hospital_id}/beds", json={"available": 2}, headers=doctor_headers).status_code == 200
    updated = client.get("/api/hospitals").json["hospitals"][0]
    assert updated["available"] == 2
    assert "Simulated" in updated["availability_label"]
    assert client.patch(f"/api/hospitals/{hospital_id}/beds", json={"available": -1}, headers=doctor_headers).status_code == 400
