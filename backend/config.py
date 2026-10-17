"""Application configuration module."""
import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
# Load environment variables from .env file if present
load_dotenv(BASE_DIR / ".env")


class Settings(BaseModel):
    PROJECT_NAME: str = "ClaimGuard"
    VERSION: str = "0.1.0"
    API_PREFIX: str = "/api"

    # Server network settings
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Storage settings
    SQLITE_FILE: str = str(BASE_DIR / "claimguard.db")
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{SQLITE_FILE}")

    # Execution & Platform settings
    # Options: LOCAL_MOCK | IBM_LINUXONE
    EXECUTION_TARGET: str = os.getenv("EXECUTION_TARGET", "LOCAL_MOCK")

    # Pre-trained ML model artifact path
    MODEL_PATH: str = os.getenv("MODEL_PATH", str(BASE_DIR / "backend" / "ml" / "model.joblib"))

    # Business logic & thresholds
    DUPLICATE_WINDOW_DAYS: int = int(os.getenv("DUPLICATE_WINDOW_DAYS", "30"))
    ANOMALY_THRESHOLD_SCORE: float = float(os.getenv("ANOMALY_THRESHOLD_SCORE", "60.0"))

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


settings = Settings()
