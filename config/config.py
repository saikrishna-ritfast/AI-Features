import os
from pathlib import Path
from dotenv import load_dotenv

# Locate project root folder (.env is next to app folder)
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environmental variables from .env file at the project root
load_dotenv(dotenv_path=BASE_DIR / ".env")

class Settings:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    ALLOWED_EXTENSIONS: set = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm"}

settings = Settings()
