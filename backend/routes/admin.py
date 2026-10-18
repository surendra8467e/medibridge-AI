from flask import Blueprint, g, jsonify, request
from werkzeug.security import check_password_hash
from database.db import get_db
from .common import issue_admin_token, require_admin

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")
ALLOWED_STATUSES = {"pending", "verified", "rejected"}


@admin_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    admin = get_db().execute("SELECT id,email,password_hash FROM demo_admins WHERE lower(email)=?", (email,)).fetchone()
    if admin is None or not check_password_hash(admin["password_hash"], password):
        return jsonify(error="Administrator email or password is incorrect"), 401
    return jsonify(token=issue_admin_token(admin["id"]), user={"id": admin["id"], "email": admin["email"], "role": "admin", "name": "Demo administrator"})


@admin_bp.get("/me")
@require_admin
def me():
    return jsonify(user={**g.admin, "role": "admin", "name": "Demo administrator"})


@admin_bp.get("/doctors")
@require_admin
def list_doctors():
    rows = get_db().execute("""SELECT u.id,u.name,u.email,p.specialty,p.qualification,p.experience,
        p.verification_status,p.verification_note FROM users u JOIN doctor_profiles p ON p.user_id=u.id
        ORDER BY u.name""").fetchall()
    return jsonify(doctors=[dict(row) for row in rows])


@admin_bp.patch("/doctors/<int:doctor_id>/verification")
@require_admin
def set_verification_status(doctor_id):
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    note = str(data.get("note", "")).strip()[:1000]
    if status not in ALLOWED_STATUSES:
        return jsonify(error="Status must be pending, verified, or rejected"), 400
    db = get_db()
    profile = db.execute("SELECT verification_status FROM doctor_profiles WHERE user_id=?", (doctor_id,)).fetchone()
    if profile is None:
        return jsonify(error="Doctor profile not found"), 404
    previous_status = profile["verification_status"]
    db.execute("UPDATE doctor_profiles SET verification_status=?,verification_note=?,verified=? WHERE user_id=?",
               (status, note, int(status == "verified"), doctor_id))
    db.execute("""INSERT INTO doctor_verification_events(doctor_id,admin_id,previous_status,new_status,note)
        VALUES(?,?,?,?,?)""", (doctor_id, g.admin["id"], previous_status, status, note))
    db.commit()
    return jsonify(doctor={"id": doctor_id, "verificationStatus": status, "verificationNote": note})


@admin_bp.get("/doctors/<int:doctor_id>/verification-events")
@require_admin
def verification_events(doctor_id):
    rows = get_db().execute("""SELECT e.id,e.previous_status,e.new_status,e.note,e.created_at,a.email AS reviewed_by
        FROM doctor_verification_events e JOIN demo_admins a ON a.id=e.admin_id
        WHERE e.doctor_id=? ORDER BY e.id DESC""", (doctor_id,)).fetchall()
    return jsonify(events=[dict(row) for row in rows])