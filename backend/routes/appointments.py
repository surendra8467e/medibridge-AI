from flask import Blueprint, current_app, g, jsonify, request
from hashlib import sha256
import hmac
from database.db import get_db
from .common import require_auth

appointments_bp = Blueprint("appointments", __name__, url_prefix="/api/appointments")


@appointments_bp.get("")
@require_auth()
def list_appointments():
    db = get_db()
    if g.user["role"] == "patient":
        rows = db.execute("""SELECT a.*,p.name AS doctor_name FROM appointments a JOIN users p ON p.id=a.doctor_id
                            WHERE a.patient_id=? ORDER BY a.id DESC""", (g.user["id"],)).fetchall()
    else:
        if not g.user.get("doctor_verified", False):
            return jsonify(error="Doctor verification is required to view patient appointments"), 403
        rows = db.execute("""SELECT a.*,p.name AS patient_name FROM appointments a JOIN users p ON p.id=a.patient_id
                            WHERE a.doctor_id=? ORDER BY a.id DESC""", (g.user["id"],)).fetchall()
    return jsonify(appointments=[dict(row) for row in rows])


@appointments_bp.post("")
@require_auth("patient")
def create_appointment():
    data = request.get_json(silent=True) or {}
    doctor_id = data.get("doctor_id")
    reason = str(data.get("reason", "")).strip()
    scheduled_at = str(data.get("scheduled_at", "")).strip()
    if not isinstance(doctor_id, int) or not reason or not scheduled_at or len(reason) > 1000:
        return jsonify(error="Doctor, reason, and requested date/time are required"), 400
    db = get_db()
    doctor = db.execute("SELECT verification_status FROM doctor_profiles WHERE user_id=?", (doctor_id,)).fetchone()
    if doctor is None:
        return jsonify(error="Doctor not found"), 404
    if doctor["verification_status"] != "verified":
        return jsonify(error="This doctor's demo profile is awaiting verification"), 409
    cursor = db.execute("INSERT INTO appointments(patient_id,doctor_id,reason,scheduled_at) VALUES(?,?,?,?)", (g.user["id"], doctor_id, reason, scheduled_at))
    db.commit()
    return jsonify(appointment={"id": cursor.lastrowid, "status": "requested"}), 201


@appointments_bp.patch("/<int:appointment_id>")
@require_auth("doctor", verified_doctor=True)
def update_appointment(appointment_id):
    status = (request.get_json(silent=True) or {}).get("status")
    if status not in ("accepted", "declined", "completed"):
        return jsonify(error="Status must be accepted, declined, or completed"), 400
    db = get_db()
    cursor = db.execute("UPDATE appointments SET status=? WHERE id=? AND doctor_id=?", (status, appointment_id, g.user["id"]))
    if cursor.rowcount == 0:
        return jsonify(error="Appointment not found or not assigned to you"), 404
    if status == "accepted":
        row = db.execute("SELECT patient_id,doctor_id FROM appointments WHERE id=?", (appointment_id,)).fetchone()
        db.execute("INSERT OR IGNORE INTO assignments(patient_id,doctor_id) VALUES(?,?)", (row["patient_id"], row["doctor_id"]))
    db.commit()
    return jsonify(message="Appointment updated", status=status)


@appointments_bp.post("/<int:appointment_id>/cancel")
@require_auth("patient")
def cancel_appointment(appointment_id):
    db = get_db()
    cursor = db.execute("UPDATE appointments SET status='cancelled' WHERE id=? AND patient_id=? AND status IN ('requested','accepted')",
                        (appointment_id, g.user["id"]))
    if cursor.rowcount == 0:
        return jsonify(error="Appointment not found or no longer cancellable"), 404
    db.commit()
    return jsonify(message="Appointment cancelled", status="cancelled")


@appointments_bp.get("/<int:appointment_id>/video-room")
@require_auth()
def video_room(appointment_id):
    db = get_db()
    appointment = db.execute("SELECT id,patient_id,doctor_id,status FROM appointments WHERE id=?", (appointment_id,)).fetchone()
    if appointment is None:
        return jsonify(error="Appointment not found"), 404
    if g.user["id"] not in (appointment["patient_id"], appointment["doctor_id"]):
        return jsonify(error="You are not a participant in this appointment"), 403
    if appointment["status"] not in ("accepted", "completed"):
        return jsonify(error="A video room is available after the doctor accepts the request"), 409
    signature = hmac.new(current_app.config["SECRET_KEY"].encode(), str(appointment_id).encode(), sha256).hexdigest()[:12]
    return jsonify(url=f"https://meet.jit.si/medibridge-demo-{appointment_id}-{signature}", mode="external demo link",
                   notice="Jitsi is an external public service. Do not share sensitive medical information in this demo room.")
