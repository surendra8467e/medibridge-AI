from functools import wraps
from flask import current_app, g, jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from database.db import get_db


def issue_token(user_id):
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"]).dumps({"user_id": user_id})


def issue_admin_token(admin_id):
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"]).dumps({"admin_id": admin_id})


def require_auth(role=None, verified_doctor=False):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            token = request.headers.get("Authorization", "").removeprefix("Bearer ")
            if not token:
                return jsonify(error="Authentication required"), 401
            try:
                data = URLSafeTimedSerializer(current_app.config["SECRET_KEY"]).loads(
                    token, max_age=current_app.config["TOKEN_MAX_AGE"])
            except (BadSignature, SignatureExpired):
                return jsonify(error="Invalid or expired session"), 401
            if not isinstance(data, dict) or not isinstance(data.get("user_id"), int):
                return jsonify(error="Invalid or expired session"), 401
            user = get_db().execute("SELECT id,name,email,role,language FROM users WHERE id=?", (data["user_id"],)).fetchone()
            if user is None:
                return jsonify(error="Account not found"), 401
            g.user = dict(user)
            if g.user["role"] == "doctor":
                profile = get_db().execute("SELECT verification_status,verification_note FROM doctor_profiles WHERE user_id=?", (g.user["id"],)).fetchone()
                status = profile["verification_status"] if profile else "pending"
                g.user["verificationStatus"] = status
                g.user["verificationNote"] = profile["verification_note"] if profile else ""
                g.user["doctor_verified"] = status == "verified"
            if role and g.user["role"] != role:
                return jsonify(error="This action is not allowed for your role"), 403
            if verified_doctor and not g.user.get("doctor_verified", False):
                return jsonify(error="Doctor verification is required for this action"), 403
            return view(*args, **kwargs)
        return wrapped
    return decorator


def require_admin(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        token = request.headers.get("Authorization", "").removeprefix("Bearer ")
        if not token:
            return jsonify(error="Administrator authentication required"), 401
        try:
            data = URLSafeTimedSerializer(current_app.config["SECRET_KEY"]).loads(
                token, max_age=current_app.config["TOKEN_MAX_AGE"])
        except (BadSignature, SignatureExpired):
            return jsonify(error="Invalid or expired administrator session"), 401
        if not isinstance(data, dict) or not isinstance(data.get("admin_id"), int):
            return jsonify(error="Administrator access required"), 403
        admin = get_db().execute("SELECT id,email FROM demo_admins WHERE id=?", (data["admin_id"],)).fetchone()
        if admin is None:
            return jsonify(error="Administrator account not found"), 401
        g.admin = dict(admin)
        return view(*args, **kwargs)
    return wrapped


def json_error(message, status):
    return jsonify(error=message), status
