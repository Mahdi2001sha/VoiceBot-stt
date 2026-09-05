"""
JOB: take a saved audio file - it doesn't matter whether it came from
upload_input.py or recorder_input.py - and turn it into text, by calling
the WhisperLiveKit ("wlk") engine's REST endpoint.

Only knows: a file path goes in, a string comes out. This is what makes
it reusable from both input sources, and easy to swap for a different
engine later without touching anything else in the pipeline.
"""
import asyncio
from pathlib import Path

import httpx

from config import MAX_CONCURRENT_TRANSCRIPTIONS, TRANSCRIBE_TIMEOUT_SECONDS, WHISPER_API_URL, WHISPER_BASE_URL

# Caps how many files are being transcribed by the engine at the same
# moment. The engine (e.g. large-v3 on CPU) is the real bottleneck, not
# this project - see MAX_CONCURRENT_TRANSCRIPTIONS in .env.
_semaphore = asyncio.Semaphore(MAX_CONCURRENT_TRANSCRIPTIONS)


async def check_engine_online() -> bool:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{WHISPER_BASE_URL}/health")
            return r.status_code == 200
    except Exception:
        return False


async def transcribe_file(audio_path: Path, language: str) -> str:
    """
    Sends the audio at audio_path to wlk and returns the transcribed text.
    Raises RuntimeError with a human-readable message on failure.
    """
    content = Path(audio_path).read_bytes()

    try:
        async with _semaphore:
            async with httpx.AsyncClient(timeout=TRANSCRIBE_TIMEOUT_SECONDS) as client:
                files = {"file": (Path(audio_path).name, content, "application/octet-stream")}
                data = {"language": language}
                resp = await client.post(WHISPER_API_URL, files=files, data=data)
                resp.raise_for_status()
                result = resp.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 503:
            raise RuntimeError(
                "The transcription engine (wlk) is not ready yet - it may still be "
                "loading the model into memory. Wait a bit and try again."
            )
        if e.response.status_code == 408:
            raise RuntimeError(
                "The engine timed out before finishing this file (large-v3 on CPU can "
                "be slower than real-time). Try a shorter clip, a smaller model, or "
                "raise --rest-timeout on wlk and TRANSCRIBE_TIMEOUT_SECONDS in .env."
            )
        raise RuntimeError(f"Engine returned an error ({e.response.status_code}): {e.response.text[:300]}")
    except httpx.RequestError as e:
        raise RuntimeError(
            "Could not reach the transcription engine. Make sure WhisperLiveKit ('wlk') is running."
        ) from e

    return (result.get("text") or "").strip()
