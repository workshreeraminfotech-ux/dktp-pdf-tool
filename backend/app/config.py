import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR.parent / ".env")
load_dotenv(BASE_DIR / ".env")

STORAGE_DIR = BASE_DIR / "storage"

UPLOAD_DIR = STORAGE_DIR / "uploads"
PROCESSED_DIR = STORAGE_DIR / "processed"
REPORTS_DIR = STORAGE_DIR / "reports"
SNIPPETS_DIR = STORAGE_DIR / "snippets"

for d in [UPLOAD_DIR, PROCESSED_DIR, REPORTS_DIR, SNIPPETS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'deviation_intelligence.db'}")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production-99824")
CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000", "*"]
