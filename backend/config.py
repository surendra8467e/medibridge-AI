import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
DATABASE_PATH = Path(os.getenv("MEDIBRIDGE_DATABASE") or BASE_DIR / "database" / "medibridge.db").resolve()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "local-demo-secret-change-before-deployment")
    TOKEN_MAX_AGE = int(os.getenv("TOKEN_MAX_AGE", "86400"))
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    AI_API_KEY = os.getenv("AI_API_KEY", "")
    AI_API_URL = os.getenv("AI_API_URL", "https://api.openai.com/v1/chat/completions")
    AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")
    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    DATABASE_PATH = DATABASE_PATH
