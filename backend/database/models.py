from werkzeug.security import generate_password_hash
from .db import get_db


def seed_demo_data():
    db = get_db()
    demos = [
        ("Aarav Sharma", "patient@medibridge.demo", "patient", "DemoPatient123!"),
        ("Dr. Mira Kapoor", "doctor@medibridge.demo", "doctor", "DemoDoctor123!"),
    ]
    for name, email, role, password in demos:
        db.execute("INSERT OR IGNORE INTO users(name,email,password_hash,role) VALUES(?,?,?,?)",
                   (name, email, generate_password_hash(password), role))
    doctor = db.execute("SELECT id FROM users WHERE email=?", ("doctor@medibridge.demo",)).fetchone()["id"]
    patient = db.execute("SELECT id FROM users WHERE email=?", ("patient@medibridge.demo",)).fetchone()["id"]
    db.execute("INSERT OR IGNORE INTO doctor_profiles(user_id,specialty,qualification,experience,fee,verified,verification_status) VALUES(?,?,?,?,?,0,'pending')",
               (doctor, "General Physician", "Fictional demo profile", 8, 500))
    db.execute("INSERT OR IGNORE INTO demo_admins(email,password_hash) VALUES(?,?)",
               ("admin@medibridge.demo", generate_password_hash("DemoAdmin123!")))
    db.execute("INSERT OR IGNORE INTO patient_profiles(user_id,history) VALUES(?,?)", (patient, "Demo profile; no medical history shared."))
    db.execute("INSERT OR IGNORE INTO assignments(patient_id,doctor_id) VALUES(?,?)", (patient, doctor))
    hospitals = [
        ("MediBridge Demo Community Hospital", "Jaipur, Rajasthan", "Emergency, general medicine, pediatrics", 1, 1),
        ("MediBridge Demo Care Centre", "Ajmer, Rajasthan", "General medicine, diagnostics", 0, 1),
    ]
    for hospital in hospitals:
        db.execute("INSERT OR IGNORE INTO hospitals(name,location,services,emergency,demo) VALUES(?,?,?,?,?)", hospital)
    for hospital_id in db.execute("SELECT id FROM hospitals").fetchall():
        db.execute("INSERT OR IGNORE INTO bed_availability(hospital_id,available) VALUES(?,?)", (hospital_id["id"], 4))
    db.commit()
