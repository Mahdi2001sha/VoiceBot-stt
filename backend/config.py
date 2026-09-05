"""
JOB: hold every setting the project uses, and nothing else.
Reads from environment variables (.env), with sensible defaults.
No other file should call os.getenv directly - import from here instead.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ---- paths ----
BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
LOGS_DIR = ROOT_DIR / "logs"

AUDIO_DIR = LOGS_DIR / "Audio"   # every saved recording/upload
TEXT_DIR = LOGS_DIR / "Text"     # one .txt transcript per request
CSV_LOG_PATH = LOGS_DIR / "log.csv"

AUDIO_DIR.mkdir(parents=True, exist_ok=True)
TEXT_DIR.mkdir(parents=True, exist_ok=True)

# ---- whisper engine (wlk) ----
# 127.0.0.1 rather than "localhost" avoids IPv4/IPv6 resolution issues on Windows.
WHISPER_API_URL = os.getenv("WHISPER_API_URL", "http://127.0.0.1:8000/v1/audio/transcriptions")
WHISPER_BASE_URL = os.getenv("WHISPER_BASE_URL", "http://127.0.0.1:8000")
WHISPER_WS_URL = os.getenv("WHISPER_WS_URL", "ws://127.0.0.1:8000/asr")

# Informational only - the actual model is chosen when wlk itself is started
# (see start.bat). This just gets shown back via /api/health so the frontend
# / anyone integrating can see what the engine is currently supposed to be.
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "large-v3")

# ---- app behaviour ----
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "fa")
MAX_CONCURRENT_TRANSCRIPTIONS = int(os.getenv("MAX_CONCURRENT_TRANSCRIPTIONS", "2"))
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "50"))
ALLOWED_EXT = {".wav", ".mp3", ".m4a", ".ogg", ".webm", ".flac", ".mp4", ".aac"}

# How long our backend waits for wlk to respond to one transcription call.
# large-v3 on CPU can run well below real-time speed, so this needs to be
# generous - and needs to stay ABOVE whatever --rest-timeout wlk itself
# uses (see start.bat), or we'll time out on our side first.
TRANSCRIBE_TIMEOUT_SECONDS = int(os.getenv("TRANSCRIBE_TIMEOUT_SECONDS", "1800"))

# ---- server ----
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))
