from .db import get_db

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, phone TEXT UNIQUE,
 password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('patient','doctor')),
 language TEXT NOT NULL DEFAULT 'en', verified INTEGER NOT NULL DEFAULT 1,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS doctor_profiles (
 user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
 specialty TEXT NOT NULL DEFAULT 'General Physician', qualification TEXT NOT NULL DEFAULT 'Demo profile',
 experience INTEGER NOT NULL DEFAULT 0, fee INTEGER NOT NULL DEFAULT 0, verified INTEGER NOT NULL DEFAULT 0,
 verification_status TEXT NOT NULL DEFAULT 'pending', verification_note TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS demo_admins (
 id INTEGER PRIMARY KEY, email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS doctor_verification_events (
 id INTEGER PRIMARY KEY, doctor_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 admin_id INTEGER NOT NULL REFERENCES demo_admins(id), previous_status TEXT NOT NULL,
 new_status TEXT NOT NULL, note TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS patient_profiles (
 user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
 history TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS assignments (
 patient_id INTEGER NOT NULL REFERENCES users(id), doctor_id INTEGER NOT NULL REFERENCES users(id),
 PRIMARY KEY(patient_id, doctor_id)
);
CREATE TABLE IF NOT EXISTS chat_sessions (
 id INTEGER PRIMARY KEY, patient_id INTEGER NOT NULL REFERENCES users(id),
 title TEXT NOT NULL DEFAULT 'New conversation', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS chat_messages (
 id INTEGER PRIMARY KEY, session_id INTEGER NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
 sender TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS triage_assessments (
 id INTEGER PRIMARY KEY, patient_id INTEGER NOT NULL REFERENCES users(id), session_id INTEGER REFERENCES chat_sessions(id),
 symptoms TEXT NOT NULL, stage INTEGER NOT NULL, response TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS appointments (
 id INTEGER PRIMARY KEY, patient_id INTEGER NOT NULL REFERENCES users(id), doctor_id INTEGER NOT NULL REFERENCES users(id),
 reason TEXT NOT NULL, scheduled_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'requested',
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS consultations (
 id INTEGER PRIMARY KEY, appointment_id INTEGER NOT NULL UNIQUE REFERENCES appointments(id),
 notes TEXT NOT NULL DEFAULT '', assessment TEXT NOT NULL DEFAULT '', advice TEXT NOT NULL DEFAULT '',
 summary TEXT NOT NULL DEFAULT '', approved INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS messages (
 id INTEGER PRIMARY KEY, patient_id INTEGER NOT NULL REFERENCES users(id), doctor_id INTEGER NOT NULL REFERENCES users(id),
 sender_id INTEGER NOT NULL REFERENCES users(id), content TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS hospitals (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, location TEXT NOT NULL, services TEXT NOT NULL,
 emergency INTEGER NOT NULL DEFAULT 0, demo INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS bed_availability (
 hospital_id INTEGER PRIMARY KEY REFERENCES hospitals(id), available INTEGER NOT NULL,
 updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS bed_requests (
 id INTEGER PRIMARY KEY, patient_id INTEGER NOT NULL REFERENCES users(id), hospital_id INTEGER NOT NULL REFERENCES hospitals(id),
 note TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'submitted-demo', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS reports (
 id INTEGER PRIMARY KEY, patient_id INTEGER NOT NULL REFERENCES users(id), doctor_id INTEGER NOT NULL REFERENCES users(id),
 appointment_id INTEGER REFERENCES appointments(id), title TEXT NOT NULL, content TEXT NOT NULL,
 approved INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS family_members (
 id INTEGER PRIMARY KEY, patient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 name TEXT NOT NULL, date_of_birth TEXT, relationship TEXT NOT NULL, medical_info TEXT NOT NULL DEFAULT '',
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS patient_uploads (
 id INTEGER PRIMARY KEY, patient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 family_member_id INTEGER REFERENCES family_members(id) ON DELETE SET NULL, title TEXT NOT NULL,
 category TEXT NOT NULL, original_name TEXT NOT NULL, stored_name TEXT NOT NULL UNIQUE,
 mime_type TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS medicines (
 id INTEGER PRIMARY KEY, patient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 family_member_id INTEGER REFERENCES family_members(id) ON DELETE SET NULL, name TEXT NOT NULL,
 dosage TEXT NOT NULL, frequency TEXT NOT NULL, start_date TEXT NOT NULL, end_date TEXT,
 reminder_times TEXT NOT NULL DEFAULT '', prescribing_doctor TEXT NOT NULL DEFAULT '',
 source TEXT NOT NULL DEFAULT 'patient-entered', active INTEGER NOT NULL DEFAULT 1,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS medicine_logs (
 id INTEGER PRIMARY KEY, medicine_id INTEGER NOT NULL REFERENCES medicines(id) ON DELETE CASCADE,
 patient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, taken_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS bed_bookings (
 id INTEGER PRIMARY KEY, reference TEXT NOT NULL UNIQUE, patient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 family_member_id INTEGER REFERENCES family_members(id) ON DELETE SET NULL, hospital_id INTEGER NOT NULL REFERENCES hospitals(id),
 bed_type TEXT NOT NULL, patient_name TEXT NOT NULL, admission_date TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'pending-demo', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def initialize_database():
    db = get_db()
    db.executescript(SCHEMA)
    profile_columns = {row["name"] for row in db.execute("PRAGMA table_info(doctor_profiles)")}
    if "verified" not in profile_columns:
        db.execute("ALTER TABLE doctor_profiles ADD COLUMN verified INTEGER NOT NULL DEFAULT 0")
    if "verification_status" not in profile_columns:
        db.execute("ALTER TABLE doctor_profiles ADD COLUMN verification_status TEXT NOT NULL DEFAULT 'pending'")
    if "verification_note" not in profile_columns:
        db.execute("ALTER TABLE doctor_profiles ADD COLUMN verification_note TEXT NOT NULL DEFAULT ''")
    user_columns = {row["name"] for row in db.execute("PRAGMA table_info(users)")}
    if "phone" not in user_columns:
        db.execute("ALTER TABLE users ADD COLUMN phone TEXT")
    db.execute("CREATE UNIQUE INDEX IF NOT EXISTS users_phone_unique ON users(phone)")
    db.commit()
