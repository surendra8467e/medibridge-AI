from flask import Blueprint, g, jsonify, request
from database.db import get_db
from services.ai_service import respond_to_health_message
from .common import require_auth

chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")


@chat_bp.get("/sessions")
@require_auth("patient")
def sessions():
    rows = get_db().execute("SELECT id,title,created_at FROM chat_sessions WHERE patient_id=? ORDER BY id DESC", (g.user["id"],)).fetchall()
    return jsonify(sessions=[dict(row) for row in rows])


@chat_bp.post("/sessions")
@require_auth("patient")
def create_session():
    db = get_db()
    cursor = db.execute("INSERT INTO chat_sessions(patient_id,title) VALUES(?,?)", (g.user["id"], "New conversation"))
    db.commit()
    return jsonify(session={"id": cursor.lastrowid, "title": "New conversation"}), 201


@chat_bp.get("/sessions/<int:session_id>/messages")
@require_auth("patient")
def get_chat_messages(session_id):
    db = get_db()
    session = db.execute("SELECT id FROM chat_sessions WHERE id=? AND patient_id=?", (session_id, g.user["id"])).fetchone()
    if session is None:
        return jsonify(error="Conversation not found"), 404
    rows = db.execute("SELECT id,sender,content,created_at FROM chat_messages WHERE session_id=? ORDER BY id", (session_id,)).fetchall()
    return jsonify(messages=[dict(row) for row in rows])


@chat_bp.post("/sessions/<int:session_id>/messages")
@require_auth("patient")
def send_chat_message(session_id):
    content = str((request.get_json(silent=True) or {}).get("content", "")).strip()
    if not content or len(content) > 4000:
        return jsonify(error="Message must contain 1 to 4000 characters"), 400
    db = get_db()
    session = db.execute("SELECT id FROM chat_sessions WHERE id=? AND patient_id=?", (session_id, g.user["id"])).fetchone()
    if session is None:
        return jsonify(error="Conversation not found"), 404
    history_rows = db.execute("SELECT sender,content FROM chat_messages WHERE session_id=? ORDER BY id", (session_id,)).fetchall()
    result = respond_to_health_message(content, g.user["language"], [dict(row) for row in history_rows])
    db.execute("INSERT INTO chat_messages(session_id,sender,content) VALUES(?,?,?)", (session_id, "patient", content))
    db.execute("INSERT INTO chat_messages(session_id,sender,content) VALUES(?,?,?)", (session_id, "assistant", result["response"]))
    db.execute("INSERT INTO triage_assessments(patient_id,session_id,symptoms,stage,response) VALUES(?,?,?,?,?)",
               (g.user["id"], session_id, content, result["stage"], result["response"]))
    db.execute("UPDATE chat_sessions SET title=? WHERE id=? AND title='New conversation'", (content[:60], session_id))
    db.commit()
    return jsonify(reply=result, session_id=session_id), 200
