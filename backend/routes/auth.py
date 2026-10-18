import re
from flask import Blueprint, current_app, g, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash
from database.db import get_db
from .common import issue_token, require_auth

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def valid_email(email):
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email or ""))


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    name, email, password, role = (str(data.get(key, "")).strip() for key in ("name", "email", "password", "role"))
    email = email.lower()
    phone = re.sub(r"\D", "", str(data.get("phone", ""))) or None
    if not name or not valid_email(email) or len(password) < 8 or role not in ("patient", "doctor"):
        return jsonify(error="Provide a name, valid email, password of at least 8 characters, and patient or doctor role"), 400
    if phone is not None and not 7 <= len(phone) <= 15:
        return jsonify(error="Phone number must contain 7 to 15 digits"), 400
    db = get_db()
    try:
        cursor = db.execute("INSERT INTO users(name,email,phone,password_hash,role) VALUES(?,?,?,?,?)",
                    (name, email, phone, generate_password_hash(password), role))
        user_id = cursor.lastrowid
        if role == "patient":
            db.execute("INSERT INTO patient_profiles(user_id) VALUES(?)", (user_id,))
        else:
            db.execute("INSERT INTO doctor_profiles(user_id) VALUES(?)", (user_id,))
        db.commit()
    except Exception as error:
        db.rollback()
        if "UNIQUE constraint" in str(error):
            return jsonify(error="An account with this email already exists"), 409
        raise
    return jsonify(token=issue_token(user_id), user={"id": user_id, "name": name, "email": email, "role": role, "language": "en"}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    identifier = str(data.get("identifier", data.get("email", ""))).strip()
    email = identifier.lower()
    phone = re.sub(r"\D", "", identifier)
    password = str(data.get("password", ""))
    role = data.get("role")
    if role is not None and role not in ("patient", "doctor"):
        return jsonify(error="Role must be patient or doctor"), 400
    user = get_db().execute("SELECT * FROM users WHERE lower(email)=? OR phone=?", (email, phone)).fetchone()
    if user is None or not check_password_hash(user["password_hash"], password):
        return jsonify(error="Email or password is incorrect"), 401
    if role and user["role"] != role:
        return jsonify(error=f"This account is not registered as a {role}"), 403
    result = {key: user[key] for key in ("id", "name", "email", "role", "language")}
    if user["role"] == "doctor":
        profile = get_db().execute("SELECT verification_status,verification_note FROM doctor_profiles WHERE user_id=?", (user["id"],)).fetchone()
        result["verificationStatus"] = profile["verification_status"] if profile else "pending"
        result["verificationNote"] = profile["verification_note"] if profile else ""
        result["doctor_verified"] = result["verificationStatus"] == "verified"
    return jsonify(token=issue_token(user["id"]), user=result)


@auth_bp.get("/me")
@require_auth()
def me():
    return jsonify(user=g.user)


@auth_bp.patch("/language")
@require_auth()
def set_language():
    language = (request.get_json(silent=True) or {}).get("language")
    if language not in ("en", "hi"):
        return jsonify(error="Language must be en or hi"), 400
    get_db().execute("UPDATE users SET language=? WHERE id=?", (language, g.user["id"]))
    get_db().commit()
    return jsonify(language=language)


@auth_bp.post("/logout")
def logout():
    return jsonify(message="Signed out. Remove the local session token to complete logout.")
