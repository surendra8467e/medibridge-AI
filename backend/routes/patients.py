from flask import Blueprint, g, jsonify, request
from database.db import get_db
from .common import require_auth

patients_bp = Blueprint("patients", __name__, url_prefix="/api/patients")


def authorized_pair(db, patient_id, doctor_id):
    return db.execute("""SELECT 1 WHERE EXISTS(
        SELECT 1 FROM assignments WHERE patient_id=? AND doctor_id=?
    ) OR EXISTS(
        SELECT 1 FROM appointments WHERE patient_id=? AND doctor_id=? AND status IN ('accepted','completed')
    )""", (patient_id, doctor_id, patient_id, doctor_id)).fetchone() is not None


def conversation_metadata(db, patient_id, doctor_id):
    appointment = db.execute("""SELECT id FROM appointments WHERE patient_id=? AND doctor_id=?
        AND status IN ('accepted','completed') ORDER BY id DESC LIMIT 1""", (patient_id, doctor_id)).fetchone()
    return {
        "patientId": patient_id,
        "doctorId": doctor_id,
        "appointmentId": appointment["id"] if appointment else None,
        "conversationId": f"patient-{patient_id}-doctor-{doctor_id}",
    }


@patients_bp.get("/me/doctors")
@require_auth("patient")
def message_doctors():
    rows = get_db().execute("""SELECT DISTINCT u.id,u.name,u.email,p.specialty FROM users u
        JOIN doctor_profiles p ON p.user_id=u.id
        WHERE u.role='doctor' AND p.verification_status='verified' AND (
            EXISTS(SELECT 1 FROM assignments a WHERE a.patient_id=? AND a.doctor_id=u.id)
            OR EXISTS(SELECT 1 FROM appointments ap WHERE ap.patient_id=? AND ap.doctor_id=u.id AND ap.status IN ('accepted','completed'))
        ) ORDER BY u.name""", (g.user["id"], g.user["id"])).fetchall()
    return jsonify(doctors=[dict(row) for row in rows])


@patients_bp.get("/me")
@require_auth("patient")
def patient_profile():
    row = get_db().execute("SELECT history FROM patient_profiles WHERE user_id=?", (g.user["id"],)).fetchone()
    return jsonify(profile={"user": g.user, "history": row["history"] if row else ""})


@patients_bp.put("/me")
@require_auth("patient")
def update_patient_profile():
    history = str((request.get_json(silent=True) or {}).get("history", ""))[:4000]
    db = get_db()
    db.execute("INSERT INTO patient_profiles(user_id,history) VALUES(?,?) ON CONFLICT(user_id) DO UPDATE SET history=excluded.history", (g.user["id"], history))
    db.commit()
    return jsonify(message="Health history saved", history=history)


@patients_bp.get("/<int:patient_id>")
@require_auth("doctor", verified_doctor=True)
def patient_detail(patient_id):
    db = get_db()
    if not authorized_pair(db, patient_id, g.user["id"]):
        return jsonify(error="Patient is not assigned to this doctor"), 403
    row = db.execute("SELECT id,name,email FROM users WHERE id=? AND role='patient'", (patient_id,)).fetchone()
    if row is None:
        return jsonify(error="Patient not found"), 404
    profile = db.execute("SELECT history FROM patient_profiles WHERE user_id=?", (patient_id,)).fetchone()
    return jsonify(patient={**dict(row), "history": profile["history"] if profile else ""})


@patients_bp.get("/<int:patient_id>/messages")
@require_auth()
def get_messages(patient_id):
    db = get_db()
    if g.user["role"] == "doctor" and not g.user.get("doctor_verified", False):
        return jsonify(error="Doctor verification is required for this action"), 403
    if g.user["role"] == "patient":
        allowed = patient_id == g.user["id"]
        doctor_id = request.args.get("doctor_id", type=int)
        if not doctor_id or not authorized_pair(db, patient_id, doctor_id):
            return jsonify(error="Messaging becomes available after a doctor accepts your appointment request."), 403
    else:
        doctor_id = g.user["id"]
        allowed = authorized_pair(db, patient_id, doctor_id)
    if not allowed:
        return jsonify(error="You are not authorized to view this conversation"), 403
    rows = db.execute("SELECT id,patient_id,doctor_id,sender_id,content,created_at FROM messages WHERE patient_id=? AND doctor_id=? ORDER BY id", (patient_id, doctor_id)).fetchall()
    return jsonify(**conversation_metadata(db, patient_id, doctor_id), messages=[dict(row) for row in rows])


@patients_bp.post("/<int:patient_id>/messages")
@require_auth()
def send_message(patient_id):
    data = request.get_json(silent=True) or {}
    content = str(data.get("content", "")).strip()
    if not content or len(content) > 4000:
        return jsonify(error="Message must contain 1 to 4000 characters"), 400
    db = get_db()
    if g.user["role"] == "doctor" and not g.user.get("doctor_verified", False):
        return jsonify(error="Doctor verification is required for this action"), 403
    if g.user["role"] == "patient":
        if patient_id != g.user["id"]:
            return jsonify(error="You can only message as yourself"), 403
        doctor_id = data.get("doctor_id")
    else:
        doctor_id = g.user["id"]
    if not isinstance(doctor_id, int) or not authorized_pair(db, patient_id, doctor_id):
        return jsonify(error="Messaging is available only after this doctor accepts an appointment linked to your account."), 403
    cursor = db.execute("INSERT INTO messages(patient_id,doctor_id,sender_id,content) VALUES(?,?,?,?)", (patient_id, doctor_id, g.user["id"], content))
    db.commit()
    row = db.execute("SELECT id,patient_id,doctor_id,sender_id,content,created_at FROM messages WHERE id=?", (cursor.lastrowid,)).fetchone()
    return jsonify(message=dict(row), **conversation_metadata(db, patient_id, doctor_id)), 201
