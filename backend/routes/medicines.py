from flask import Blueprint, g, jsonify, request
from database.db import get_db
from .common import require_auth

medicines_bp = Blueprint("medicines", __name__, url_prefix="/api/medicines")


def parse_medicine(data):
    return {
        "name": str(data.get("name", "")).strip()[:160],
        "dosage": str(data.get("dosage", "")).strip()[:120],
        "frequency": str(data.get("frequency", "")).strip()[:120],
        "start_date": str(data.get("start_date", "")).strip()[:10],
        "end_date": str(data.get("end_date", "")).strip()[:10] or None,
        "reminder_times": str(data.get("reminder_times", "")).strip()[:500],
    }


def owned_member(db, patient_id, member_id):
    return member_id is None or db.execute("SELECT 1 FROM family_members WHERE id=? AND patient_id=?", (member_id, patient_id)).fetchone() is not None


@medicines_bp.get("")
@require_auth()
def list_medicines():
    db = get_db()
    if g.user["role"] == "patient":
        rows = db.execute("""SELECT m.*,f.name AS family_member_name,
            (SELECT COUNT(*) FROM medicine_logs l WHERE l.medicine_id=m.id) AS taken_count
            FROM medicines m LEFT JOIN family_members f ON f.id=m.family_member_id
            WHERE m.patient_id=? ORDER BY m.active DESC,m.id DESC""", (g.user["id"],)).fetchall()
    else:
        if not g.user.get("doctor_verified", False):
            return jsonify(error="Doctor verification is required for this action"), 403
        patient_id = request.args.get("patient_id", type=int)
        if not patient_id or not db.execute("SELECT 1 FROM assignments WHERE patient_id=? AND doctor_id=?", (patient_id, g.user["id"])).fetchone():
            return jsonify(error="An assigned patient is required"), 403
        rows = db.execute("SELECT * FROM medicines WHERE patient_id=? ORDER BY active DESC,id DESC", (patient_id,)).fetchall()
    return jsonify(medicines=[dict(row) for row in rows])


@medicines_bp.post("")
@require_auth("patient")
def add_patient_medicine():
    data = request.get_json(silent=True) or {}
    medicine = parse_medicine(data)
    member_id = data.get("family_member_id") or None
    if not medicine["name"] or not medicine["dosage"] or not medicine["frequency"] or not medicine["start_date"]:
        return jsonify(error="Name, dosage, frequency, and start date are required"), 400
    if member_id is not None and (not isinstance(member_id, int) or not owned_member(get_db(), g.user["id"], member_id)):
        return jsonify(error="Family member is not part of this account"), 403
    db = get_db()
    cursor = db.execute("""INSERT INTO medicines(patient_id,family_member_id,name,dosage,frequency,start_date,end_date,reminder_times,source)
        VALUES(?,?,?,?,?,?,?,?, 'patient-entered')""", (g.user["id"], member_id, medicine["name"], medicine["dosage"], medicine["frequency"], medicine["start_date"], medicine["end_date"], medicine["reminder_times"]))
    db.commit()
    return jsonify(id=cursor.lastrowid, source="patient-entered"), 201


@medicines_bp.post("/prescriptions")
@require_auth("doctor", verified_doctor=True)
def create_prescription():
    data = request.get_json(silent=True) or {}
    patient_id = data.get("patient_id")
    medicine = parse_medicine(data)
    db = get_db()
    if not isinstance(patient_id, int) or not db.execute("SELECT 1 FROM assignments WHERE patient_id=? AND doctor_id=?", (patient_id, g.user["id"])).fetchone():
        return jsonify(error="Patient is not assigned to this doctor"), 403
    if not medicine["name"] or not medicine["dosage"] or not medicine["frequency"] or not medicine["start_date"]:
        return jsonify(error="Medicine, clinician-entered dosage, frequency, and start date are required"), 400
    cursor = db.execute("""INSERT INTO medicines(patient_id,name,dosage,frequency,start_date,end_date,reminder_times,prescribing_doctor,source)
        VALUES(?,?,?,?,?,?,?,?, 'doctor-prescribed')""", (patient_id, medicine["name"], medicine["dosage"], medicine["frequency"], medicine["start_date"], medicine["end_date"], medicine["reminder_times"], g.user["name"]))
    db.commit()
    return jsonify(id=cursor.lastrowid, source="doctor-prescribed"), 201


@medicines_bp.patch("/<int:medicine_id>")
@require_auth("patient")
def update_medicine(medicine_id):
    active = (request.get_json(silent=True) or {}).get("active")
    if not isinstance(active, bool):
        return jsonify(error="Active must be true or false"), 400
    db = get_db()
    cursor = db.execute("UPDATE medicines SET active=? WHERE id=? AND patient_id=?", (int(active), medicine_id, g.user["id"]))
    if cursor.rowcount == 0:
        return jsonify(error="Medicine not found"), 404
    db.commit()
    return jsonify(message="Medicine status updated")


@medicines_bp.post("/<int:medicine_id>/taken")
@require_auth("patient")
def mark_taken(medicine_id):
    db = get_db()
    medicine = db.execute("SELECT id FROM medicines WHERE id=? AND patient_id=? AND active=1", (medicine_id, g.user["id"])).fetchone()
    if medicine is None:
        return jsonify(error="Active medicine not found"), 404
    cursor = db.execute("INSERT INTO medicine_logs(medicine_id,patient_id) VALUES(?,?)", (medicine_id, g.user["id"]))
    db.commit()
    return jsonify(message="Dose marked as taken", log_id=cursor.lastrowid), 201
