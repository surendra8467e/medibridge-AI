from flask import Blueprint, g, jsonify
from database.db import get_db
from .common import require_auth

doctors_bp = Blueprint("doctors", __name__, url_prefix="/api/doctors")


@doctors_bp.get("/me")
@require_auth("doctor")
def my_profile():
    row = get_db().execute("""SELECT u.id,u.name,u.email,p.specialty,p.qualification,p.experience,p.fee,
        p.verification_status,p.verification_note FROM users u JOIN doctor_profiles p ON p.user_id=u.id
        WHERE u.id=?""", (g.user["id"],)).fetchone()
    if row is None:
        return jsonify(error="Doctor profile not found"), 404
    return jsonify(profile=dict(row))


@doctors_bp.get("")
def list_doctors():
    rows = get_db().execute("""SELECT u.id,u.name,p.specialty,p.qualification,p.experience,p.fee
        FROM users u JOIN doctor_profiles p ON p.user_id=u.id WHERE p.verification_status='verified' ORDER BY u.name""").fetchall()
    return jsonify(doctors=[{**dict(row), "demo": True} for row in rows])


@doctors_bp.get("/<int:doctor_id>")
def doctor_detail(doctor_id):
    row = get_db().execute("""SELECT u.id,u.name,p.specialty,p.qualification,p.experience,p.fee
        FROM users u JOIN doctor_profiles p ON p.user_id=u.id WHERE u.id=? AND p.verification_status='verified'""", (doctor_id,)).fetchone()
    if row is None:
        return jsonify(error="Doctor not found"), 404
    return jsonify(doctor={**dict(row), "demo": True})


@doctors_bp.get("/patients/assigned")
@require_auth("doctor", verified_doctor=True)
def assigned_patients():
    rows = get_db().execute("""SELECT u.id,u.name,u.email,p.history FROM assignments a
        JOIN users u ON u.id=a.patient_id LEFT JOIN patient_profiles p ON p.user_id=u.id
        WHERE a.doctor_id=? ORDER BY u.name""", (g.user["id"],)).fetchall()
    return jsonify(patients=[dict(row) for row in rows])
