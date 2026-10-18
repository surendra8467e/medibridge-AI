from flask import Blueprint, g, jsonify, request
from database.db import get_db
from .common import require_auth

family_bp = Blueprint("family", __name__, url_prefix="/api/family")


def member_payload(data):
    return {
        "name": str(data.get("name", "")).strip()[:120],
        "date_of_birth": str(data.get("date_of_birth", "")).strip()[:10] or None,
        "relationship": str(data.get("relationship", "")).strip()[:60],
        "medical_info": str(data.get("medical_info", "")).strip()[:4000],
    }


@family_bp.get("")
@require_auth("patient")
def list_family():
    rows = get_db().execute("SELECT id,name,date_of_birth,relationship,medical_info,created_at FROM family_members WHERE patient_id=? ORDER BY id", (g.user["id"],)).fetchall()
    return jsonify(members=[dict(row) for row in rows])


@family_bp.post("")
@require_auth("patient")
def add_family_member():
    data = request.get_json(silent=True) or {}
    member = member_payload(data)
    if not member["name"] or not member["relationship"]:
        return jsonify(error="Name and relationship are required"), 400
    db = get_db()
    cursor = db.execute("INSERT INTO family_members(patient_id,name,date_of_birth,relationship,medical_info) VALUES(?,?,?,?,?)",
                        (g.user["id"], member["name"], member["date_of_birth"], member["relationship"], member["medical_info"]))
    db.commit()
    return jsonify(member={"id": cursor.lastrowid, **member}), 201


@family_bp.put("/<int:member_id>")
@require_auth("patient")
def update_family_member(member_id):
    member = member_payload(request.get_json(silent=True) or {})
    if not member["name"] or not member["relationship"]:
        return jsonify(error="Name and relationship are required"), 400
    db = get_db()
    cursor = db.execute("UPDATE family_members SET name=?,date_of_birth=?,relationship=?,medical_info=? WHERE id=? AND patient_id=?",
                        (member["name"], member["date_of_birth"], member["relationship"], member["medical_info"], member_id, g.user["id"]))
    if cursor.rowcount == 0:
        return jsonify(error="Family profile not found"), 404
    db.commit()
    return jsonify(member={"id": member_id, **member})


@family_bp.delete("/<int:member_id>")
@require_auth("patient")
def delete_family_member(member_id):
    db = get_db()
    cursor = db.execute("DELETE FROM family_members WHERE id=? AND patient_id=?", (member_id, g.user["id"]))
    if cursor.rowcount == 0:
        return jsonify(error="Family profile not found"), 404
    db.commit()
    return jsonify(message="Family profile removed. Its records remain in your account but are no longer linked to that member.")
