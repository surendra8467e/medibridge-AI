from flask import Flask, jsonify
from werkzeug.exceptions import RequestEntityTooLarge
from flask_cors import CORS
from config import Config
from database.db import init_app
from database.init_db import initialize_database
from database.models import seed_demo_data
from routes.auth import auth_bp
from routes.patients import patients_bp
from routes.doctors import doctors_bp
from routes.chat import chat_bp
from routes.appointments import appointments_bp
from routes.consultations import consultations_bp
from routes.hospitals import hospitals_bp
from routes.reports import reports_bp
from routes.family import family_bp
from routes.medicines import medicines_bp
from routes.admin import admin_bp


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
    if test_config:
        app.config.update(test_config)
    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}}, supports_credentials=False)
    init_app(app)
    for blueprint in (auth_bp, patients_bp, doctors_bp, chat_bp, appointments_bp, consultations_bp, hospitals_bp, reports_bp, family_bp, medicines_bp, admin_bp):
        app.register_blueprint(blueprint)

    @app.get("/api/health")
    def health():
        return jsonify(status="ok", service="MediBridge AI API")

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify(error="Endpoint or record not found"), 404

    @app.errorhandler(500)
    def server_error(_error):
        app.logger.exception("Unhandled request error")
        return jsonify(error="An unexpected server error occurred"), 500

    @app.errorhandler(RequestEntityTooLarge)
    def upload_too_large(_error):
        return jsonify(error="Uploads are limited to 10 MB"), 413

    with app.app_context():
        initialize_database()
        seed_demo_data()
    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
