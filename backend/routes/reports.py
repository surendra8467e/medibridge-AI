from pathlib import Path
from uuid import uuid4
from flask import Blueprint, current_app, g, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename
from database.db import get_db
from .common import require_auth

reports_bp = Blueprint("reports", __name__, url_prefix="/api/reports")
ALLOWED_FILES = {"pdf": "application/pdf", "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}
UPLOAD_DIRECTORY = Path(__file__).resolve().parents[1] / "private_uploads"
CATEGORIES = {"lab", "imaging", "consultation", "other"}


@reports_bp.get("")
@require_auth()
def list_reports():
    db = get_db()
    if g.user["role"] == "doctor" and not g.user.get("doctor_verified", False):
        return jsonify(error="Doctor verification is required for this action"), 403
    if g.user["role"] == "patient":
        rows = db.execute("SELECT id,title,content,created_at FROM reports WHERE patient_id=? AND approved=1 ORDER BY id DESC", (g.user["id"],)).fetchall()
    else:
        rows = db.execute("SELECT r.id,r.title,r.content,r.created_at,r.patient_id FROM reports r JOIN assignments a ON a.patient_id=r.patient_id AND a.doctor_id=r.doctor_id WHERE r.doctor_id=? ORDER BY r.id DESC", (g.user["id"],)).fetchall()
    return jsonify(reports=[dict(row) for row in rows])


@reports_bp.get("/uploads")
@require_auth("patient")
def list_uploads():
    rows = get_db().execute("""SELECT u.id,u.title,u.category,u.original_name,u.mime_type,u.family_member_id,
        u.created_at,f.name AS family_member_name FROM patient_uploads u
        LEFT JOIN family_members f ON f.id=u.family_member_id WHERE u.patient_id=? ORDER BY u.id DESC""", (g.user["id"],)).fetchall()
    return jsonify(uploads=[dict(row) for row in rows])


@reports_bp.post("/uploads")
@require_auth("patient")
def upload_report():
    upload = request.files.get("file")
    title = str(request.form.get("title", "")).strip()[:160]
    category = str(request.form.get("category", "other")).strip().lower()
    member_id = request.form.get("family_member_id", type=int) or None
    if upload is None or not title or category not in CATEGORIES:
        return jsonify(error="A report file, title, and valid category are required"), 400
    original_name = secure_filename(upload.filename or "")
    suffix = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""
    if suffix not in ALLOWED_FILES or upload.mimetype != ALLOWED_FILES[suffix]:
        return jsonify(error="Upload a PDF, PNG, or JPEG report"), 400
    signature = upload.stream.read(8)
    upload.stream.seek(0)
    signatures = {"pdf": signature.startswith(b"%PDF-"), "png": signature.startswith(b"\x89PNG\r\n\x1a\n"), "jpg": signature.startswith(b"\xff\xd8\xff"), "jpeg": signature.startswith(b"\xff\xd8\xff")}
    if not signatures[suffix]:
        return jsonify(error="File contents do not match the selected report type"), 400
    if member_id is not None and not get_db().execute("SELECT 1 FROM family_members WHERE id=? AND patient_id=?", (member_id, g.user["id"])).fetchone():
        return jsonify(error="Family member is not part of this account"), 403
    stored_name = f"{uuid4().hex}.{suffix}"
    upload_directory = Path(current_app.config.get("UPLOAD_DIRECTORY", UPLOAD_DIRECTORY))
    upload_directory.mkdir(parents=True, exist_ok=True)
    upload.save(upload_directory / stored_name)
    db = get_db()
    cursor = db.execute("""INSERT INTO patient_uploads(patient_id,family_member_id,title,category,original_name,stored_name,mime_type)
        VALUES(?,?,?,?,?,?,?)""", (g.user["id"], member_id, title, category, original_name, stored_name, ALLOWED_FILES[suffix]))
    db.commit()
    return jsonify(upload={"id": cursor.lastrowid, "title": title, "category": category, "original_name": original_name, "mime_type": ALLOWED_FILES[suffix]}), 201


@reports_bp.get("/uploads/<int:upload_id>/file")
@require_auth("patient")
def download_report(upload_id):
    row = get_db().execute("SELECT stored_name,original_name,mime_type FROM patient_uploads WHERE id=? AND patient_id=?", (upload_id, g.user["id"])).fetchone()
    if row is None:
        return jsonify(error="Report not found"), 404
    upload_directory = Path(current_app.config.get("UPLOAD_DIRECTORY", UPLOAD_DIRECTORY))
    if not (upload_directory / row["stored_name"]).is_file():
        return jsonify(error="Report file is missing from private storage"), 404
    response = send_from_directory(upload_directory, row["stored_name"], mimetype=row["mime_type"], as_attachment=False, download_name=row["original_name"])
    response.cache_control.private = True
    response.cache_control.no_store = True
    return response
