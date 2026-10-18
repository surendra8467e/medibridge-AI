from flask import Blueprint, g, jsonify, request
from database.db import get_db
from .common import require_auth

consultations_bp = Blueprint("consultations", __name__, url_prefix="/api/consultations")


@consultations_bp.post("")
@require_auth("doctor", verified_doctor=True)
def save_consultation():
    data = request.get_json(silent=True) or {}
    appointment_id = data.get("appointment_id")
    db = get_db()
    appointment = db.execute("SELECT * FROM appointments WHERE id=? AND doctor_id=?", (appointment_id, g.user["id"])).fetchone()
    if appointment is None:
        return jsonify(error="Appointment not found or unauthorized"), 404
    fields = {key: str(data.get(key, "")).strip()[:4000] for key in ("notes", "assessment", "advice")}
    summary = "\n".join(value for value in (fields["notes"], fields["assessment"], fields["advice"]) if value)
    db.execute("""INSERT INTO consultations(appointment_id,notes,assessment,advice,summary,approved)
        VALUES(?,?,?,?,?,0) ON CONFLICT(appointment_id) DO UPDATE SET notes=excluded.notes,
        assessment=excluded.assessment,advice=excluded.advice,summary=excluded.summary,approved=0,updated_at=CURRENT_TIMESTAMP""",
        (appointment_id, fields["notes"], fields["assessment"], fields["advice"], summary))
    db.commit()
    return jsonify(summary=summary, status="draft", message="Draft saved; doctor approval is required"), 201


@consultations_bp.post("/<int:appointment_id>/approve")
@require_auth("doctor", verified_doctor=True)
def approve_consultation(appointment_id):
    db = get_db()
    row = db.execute("SELECT a.patient_id,c.summary FROM appointments a JOIN consultations c ON c.appointment_id=a.id WHERE a.id=? AND a.doctor_id=?", (appointment_id, g.user["id"])).fetchone()
    if row is None:
        return jsonify(error="Consultation draft not found"), 404
    updated = db.execute("UPDATE consultations SET approved=1 WHERE appointment_id=? AND approved=0", (appointment_id,))
    if updated.rowcount:
        db.execute("INSERT INTO reports(patient_id,doctor_id,appointment_id,title,content,approved) VALUES(?,?,?,?,?,1)",
                   (row["patient_id"], g.user["id"], appointment_id, "Consultation summary", row["summary"]))
    db.commit()
    return jsonify(message="Summary approved and shared with the patient")


@consultations_bp.get("")
@require_auth()
def list_consultations():
    db = get_db()
    if g.user["role"] == "doctor" and not g.user.get("doctor_verified", False):
        return jsonify(error="Doctor verification is required for this action"), 403
    if g.user["role"] == "patient":
        rows = db.execute("""SELECT c.*,a.scheduled_at FROM consultations c JOIN appointments a ON a.id=c.appointment_id
                            WHERE a.patient_id=? AND c.approved=1 ORDER BY c.updated_at DESC""", (g.user["id"],)).fetchall()
    else:
        rows = db.execute("""SELECT c.*,a.scheduled_at,a.patient_id FROM consultations c JOIN appointments a ON a.id=c.appointment_id
                            WHERE a.doctor_id=? ORDER BY c.updated_at DESC""", (g.user["id"],)).fetchall()
    return jsonify(consultations=[dict(row) for row in rows])
