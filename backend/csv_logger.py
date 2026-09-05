"""
JOB: append one row per request to logs/log.csv. This is the audit trail
for the whole pipeline - filename, source (upload/recording), language,
how long it took, and the full output text - whether it succeeded or not.

Deliberately a plain .csv (not a database or JSON log) so it's easy to
open in Excel, or point a separate script / LLM agent at it later.
"""
import csv
from datetime import datetime
from threading import Lock

from config import CSV_LOG_PATH

_FIELDS = [
    "timestamp",
    "request_id",
    "source",           # upload | recording
    "client_ip",
    "audio_filename",    # YYYYMMDDHHMMSS_ID.ext
    "text_filename",      # YYYYMMDDHHMMSS_ID.txt
    "language",
    "status",              # success | rejected | error
    "elapsed_seconds",
    "text",                  # the full transcribed output text
    "error_message",
]

_lock = Lock()  # keeps concurrent requests from interleaving writes


def _ensure_header() -> None:
    if not CSV_LOG_PATH.exists() or CSV_LOG_PATH.stat().st_size == 0:
        with open(CSV_LOG_PATH, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=_FIELDS).writeheader()


def log_row(**fields) -> None:
    """
    Appends one row to log.csv. Any field you don't pass is left blank.

    Example:
        log_row(request_id="a1b2c3d4", source="upload", status="success",
                audio_filename="20260813120000_a1b2c3d4.wav", text="...")
    """
    row = {key: fields.get(key, "") for key in _FIELDS}
    row["timestamp"] = datetime.now().isoformat(timespec="seconds")

    with _lock:
        _ensure_header()
        with open(CSV_LOG_PATH, "a", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=_FIELDS).writerow(row)
