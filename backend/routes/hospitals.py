from datetime import date
from secrets import token_hex
from flask import Blueprint, g, jsonify, request
from database.db import get_db
from .common import require_auth

hospitals_bp = Blueprint("hospitals", __name__, url_prefix="/api/hospitals")


@hospitals_bp.get("")
def list_hospitals():
    rows = get_db().execute("""SELECT h.*,b.available,b.updated_at FROM hospitals h
        LEFT JOIN bed_availability b ON b.hospital_id=h.id ORDER BY h.name""").fetchall()
    beds = []
    for row in rows:
        hospital = dict(row)
        count = hospital.get("available") or 0
        hospital["bed_types"] = [
            {"type": "General ward", "available": count, "estimated_cost": 1800},
            {"type": "Private room", "available": max(0, count // 2), "estimated_cost": 5200},
            {"type": "ICU", "available": max(0, count // 4), "estimated_cost": 9800},
        ]
        hospital["availability_label"] = "Simulated demo data · not live"
        hospital["estimated_cost_label"] = "Illustrative demo estimate · not a quote"
        beds.append(hospital)
    return jsonify(hospitals=beds)


@hospitals_bp.post("/<int:hospital_id>/requests")
@require_auth("patient")
def request_bed(hospital_id):
    note = str((request.get_json(silent=True) or {}).get("note", "")).strip()[:1000]
    db = get_db()
    if not db.execute("SELECT 1 FROM hospitals WHERE id=?", (hospital_id,)).fetchone():
        return jsonify(error="Hospital not found"), 404
    cursor = db.execute("INSERT INTO bed_requests(patient_id,hospital_id,note) VALUES(?,?,?)", (g.user["id"], hospital_id, note))
    db.commit()
    return jsonify(request={"id": cursor.lastrowid, "status": "submitted-demo"}, message="Demo inquiry submitted; no bed is reserved"), 201


@hospitals_bp.get("/requests")
@require_auth()
def list_requests():
    if g.user["role"] != "patient":
        return jsonify(error="Only patient requests are available in this demo"), 403
    rows = get_db().execute("""SELECT r.id,r.status,r.note,r.created_at,h.name AS hospital_name
        FROM bed_requests r JOIN hospitals h ON h.id=r.hospital_id WHERE r.patient_id=? ORDER BY r.id DESC""", (g.user["id"],)).fetchall()
    return jsonify(requests=[dict(row) for row in rows])


@hospitals_bp.patch("/<int:hospital_id>/beds")
@require_auth("doctor", verified_doctor=True)
def update_beds(hospital_id):
    available = (request.get_json(silent=True) or {}).get("available")
    if not isinstance(available, int) or available < 0 or available > 10000:
        return jsonify(error="Available bed count must be an integer from 0 to 10000"), 400
    db = get_db()
    if not db.execute("SELECT 1 FROM hospitals WHERE id=?", (hospital_id,)).fetchone():
        return jsonify(error="Hospital not found"), 404
    db.execute("INSERT INTO bed_availability(hospital_id,available) VALUES(?,?) ON CONFLICT(hospital_id) DO UPDATE SET available=excluded.available,updated_at=CURRENT_TIMESTAMP", (hospital_id, available))
    db.commit()
    return jsonify(message="Simulated demo availability updated", available=available)


@hospitals_bp.get("/bookings")
@require_auth("patient")
def list_bookings():
    rows = get_db().execute("""SELECT b.*,h.name AS hospital_name,h.location AS hospital_location,f.name AS family_member_name
        FROM bed_bookings b JOIN hospitals h ON h.id=b.hospital_id
        LEFT JOIN family_members f ON f.id=b.family_member_id WHERE b.patient_id=? ORDER BY b.id DESC""", (g.user["id"],)).fetchall()
    return jsonify(bookings=[dict(row) for row in rows])


@hospitals_bp.post("/bookings")
@require_auth("patient")
def create_booking():
    data = request.get_json(silent=True) or {}
    hospital_id = data.get("hospital_id")
    bed_type = str(data.get("bed_type", "")).strip()
    patient_name = str(data.get("patient_name", "")).strip()[:120]
    admission_date = str(data.get("admission_date", "")).strip()[:10]
    member_id = data.get("family_member_id") or None
    if not isinstance(hospital_id, int) or bed_type not in ("General ward", "Private room", "ICU") or not patient_name:
        return jsonify(error="Hospital, supported bed type, and patient name are required"), 400
    try:
        date.fromisoformat(admission_date)
    except ValueError:
        return jsonify(error="Admission date must be a valid ISO date"), 400
    db = get_db()
    hospital = db.execute("SELECT id FROM hospitals WHERE id=?", (hospital_id,)).fetchone()
    if hospital is None:
        return jsonify(error="Hospital not found"), 404
    if member_id is not None and (not isinstance(member_id, int) or not db.execute("SELECT 1 FROM family_members WHERE id=? AND patient_id=?", (member_id, g.user["id"])).fetchone()):
        return jsonify(error="Family member is not part of this account"), 403
    reference = f"MB-{date.today():%y%m%d}-{token_hex(3).upper()}"
    cursor = db.execute("""INSERT INTO bed_bookings(reference,patient_id,family_member_id,hospital_id,bed_type,patient_name,admission_date)
        VALUES(?,?,?,?,?,?,?)""", (reference, g.user["id"], member_id, hospital_id, bed_type, patient_name, admission_date))
    db.commit()
    return jsonify(booking={"id": cursor.lastrowid, "reference": reference, "status": "pending-demo",
                           "message": "Demo booking request received. This does not reserve or confirm a hospital bed."}), 201


@hospitals_bp.patch("/bookings/<reference>")
@require_auth("patient")
def cancel_booking(reference):
    db = get_db()
    cursor = db.execute("UPDATE bed_bookings SET status='cancelled-demo' WHERE reference=? AND patient_id=? AND status='pending-demo'", (reference, g.user["id"]))
    if cursor.rowcount == 0:
        return jsonify(error="Pending demo booking not found"), 404
    db.commit()
    return jsonify(message="Demo request cancelled", status="cancelled-demo")
