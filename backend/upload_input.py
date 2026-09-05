"""
JOB: receive one uploaded audio FILE (a single POST, not a live stream),
validate it, and save it to logs/Audio/ under the shared naming
convention: YYYYMMDDHHMMSS_ID.<ext>

This file only knows about "a whole file arrived" - it has no idea about
live recording, transcription, or logging. speech_to_text.py picks up
from here.
"""
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import ALLOWED_EXT, AUDIO_DIR, MAX_UPLOAD_MB


def new_request_id() -> str:
    return uuid.uuid4().hex[:8]


def audio_filename_for(request_id: str, ext: str) -> str:
    """YYYYMMDDHHMMSS_ID.<ext> - the naming convention used everywhere in this project."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{timestamp}_{request_id}{ext}"


def validate_audio(filename: str, content: bytes) -> str:
    """Checks extension + size. Returns the lowercase extension, or raises ValueError."""
    ext = Path(filename or "").suffix.lower()
    if ext not in ALLOWED_EXT:
        raise ValueError(f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXT))}")

    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_UPLOAD_MB:
        raise ValueError(f"File too large ({size_mb:.1f} MB). Limit is {MAX_UPLOAD_MB} MB.")
    if len(content) == 0:
        raise ValueError("Uploaded file is empty.")
    return ext


def receive_upload(filename: str, content: bytes) -> dict:
    """
    Validates and saves one uploaded audio file.

    Returns:
        {request_id, filename, path, original_filename, size_mb}
    Raises ValueError if the audio is invalid.
    """
    ext = validate_audio(filename, content)
    request_id = new_request_id()
    saved_name = audio_filename_for(request_id, ext)
    saved_path = AUDIO_DIR / saved_name
    saved_path.write_bytes(content)

    return {
        "request_id": request_id,
        "filename": saved_name,
        "path": saved_path,
        "original_filename": filename,
        "size_mb": round(len(content) / (1024 * 1024), 3),
    }


def find_audio(request_id: str) -> Optional[Path]:
    matches = list(AUDIO_DIR.glob(f"*_{request_id}.*"))
    return matches[0] if matches else None
