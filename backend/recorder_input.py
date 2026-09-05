"""
JOB: everything specific to LIVE recording, as opposed to a plain file
upload (see upload_input.py). Two responsibilities:

  1. relay_live_preview() - while the user is talking, proxy their
     microphone audio straight through to wlk's native live WebSocket
     (ws://.../asr) and relay wlk's partial-transcript messages back to
     the browser, so the UI can show text updating in real time.
     This is a PREVIEW ONLY - nothing is saved or logged at this point.

  2. save_final_recording() - once the user presses "pause"/stop, the
     browser sends the complete recorded audio as one file. This saves
     it under the same YYYYMMDDHHMMSS_ID.<ext> convention used by
     upload_input.py, so it can go through the exact same speech_to_text
     -> text_output -> csv_logger pipeline afterwards for the final,
     authoritative transcript (full-context decoding is more accurate
     than the live streaming preview).
"""
import asyncio
import uuid
from typing import Optional

import websockets
from fastapi import WebSocket, WebSocketDisconnect

from config import WHISPER_WS_URL
from upload_input import audio_filename_for, validate_audio
from config import AUDIO_DIR


def new_session_id() -> str:
    """One ID shared by the live preview connection AND the final saved file."""
    return uuid.uuid4().hex[:8]


async def relay_live_preview(client_ws: WebSocket) -> None:
    """
    Runs for the lifetime of one live-recording WebSocket connection.
    Forwards binary audio chunks from the browser to wlk, and forwards
    wlk's JSON transcript messages back to the browser. Returns when
    either side disconnects.
    """
    try:
        async with websockets.connect(WHISPER_WS_URL, max_size=None) as engine_ws:

            async def browser_to_engine():
                try:
                    while True:
                        chunk = await client_ws.receive_bytes()
                        await engine_ws.send(chunk)
                except (WebSocketDisconnect, websockets.exceptions.ConnectionClosed):
                    pass

            async def engine_to_browser():
                try:
                    async for message in engine_ws:
                        # wlk sends JSON text frames describing the current
                        # transcript state - just relay them as-is, the
                        # frontend parses whatever fields are present.
                        await client_ws.send_text(message)
                except (WebSocketDisconnect, websockets.exceptions.ConnectionClosed):
                    pass

            await asyncio.gather(browser_to_engine(), engine_to_browser())
    except Exception:
        # Engine unreachable, or the browser closed before we even connected -
        # nothing to save here (live preview is best-effort), just stop quietly.
        pass


def save_final_recording(session_id: str, filename: str, content: bytes) -> dict:
    """
    Saves the complete recording once the user hits pause/stop.
    Same shape/return value as upload_input.receive_upload(), so both can
    feed into speech_to_text.py identically.
    """
    ext = validate_audio(filename, content)
    saved_name = audio_filename_for(session_id, ext)
    saved_path = AUDIO_DIR / saved_name
    saved_path.write_bytes(content)

    return {
        "request_id": session_id,
        "filename": saved_name,
        "path": saved_path,
        "original_filename": filename,
        "size_mb": round(len(content) / (1024 * 1024), 3),
    }
