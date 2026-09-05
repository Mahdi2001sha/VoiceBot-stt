"""
JOB: take the text produced by speech_to_text.py, save it to logs/Text/,
and build the final result dict that gets shown to the user / returned
by the API. Nothing here knows about audio or the engine.
"""
from pathlib import Path
from typing import Optional

from config import TEXT_DIR


def save_text(request_id: str, audio_filename: str, text: str) -> Path:
    """
    Saves text to logs/Text/<same base name as the audio file>.txt
    so the audio and text files are easy to match up by name.
    """
    base_name = Path(audio_filename).stem  # "20260813120000_a1b2c3d4"
    text_path = TEXT_DIR / f"{base_name}.txt"
    text_path.write_text(text, encoding="utf-8")
    return text_path


def find_text(request_id: str) -> Optional[Path]:
    matches = list(TEXT_DIR.glob(f"*_{request_id}.txt"))
    return matches[0] if matches else None


def build_result(request_id: str, text: str, language: str, elapsed_seconds: float, audio_filename: str, text_filename: str) -> dict:
    """Shapes the final response object returned to the frontend / API caller."""
    return {
        "request_id": request_id,
        "text": text,
        "language": language,
        "elapsed_seconds": elapsed_seconds,
        "audio_file": audio_filename,
        "text_file": text_filename,
    }
