"""
MAIN - the single hub that connects every stage of the pipeline, and the
one file to import from if you're integrating this project into
something bigger later (a chatbot, an LLM agent, another API).
See API_INTEGRATION.md for the full external API reference.

Two pipelines share the same conversion/output/logging stages:

  UPLOAD (one file, one request):
    audio bytes -> upload_input.receive_upload -> speech_to_text.transcribe_file
                -> text_output.save_text -> csv_logger.log_row

  RECORDING (live preview while talking, saved once "pause" is pressed):
    mic audio  -> recorder_input.relay_live_preview   (live text preview only)
    full blob  -> recorder_input.save_final_recording -> speech_to_text.transcribe_file
                -> text_output.save_text -> csv_logger.log_row

For LLM/chatbot integration without any HTTP involved at all, call:

    from main import process_upload
    result = await process_upload(audio_bytes, "voice.wav", language="fa")
    print(result["text"])
"""
import time

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import csv_logger
import recorder_input
import speech_to_text
import text_output
import upload_input
from config import DEFAULT_LANGUAGE, DEFAULT_MODEL, FRONTEND_DIR


# ---------------------------------------------------------------------------
# Shared pipeline runner - both entry points below call this
# ---------------------------------------------------------------------------
async def _run_pipeline(audio: dict, language: str, source: str, client_ip: str) -> dict:
    start = time.time()
    try:
        text = await speech_to_text.transcribe_file(audio["path"], language)
    except RuntimeError as e:
        csv_logger.log_row(
            request_id=audio["request_id"],
            source=source,
            client_ip=client_ip,
            audio_filename=audio["filename"],
            language=language,
            status="error",
            error_message=str(e),
        )
        raise

    text_path = text_output.save_text(audio["request_id"], audio["filename"], text)
    elapsed = round(time.time() - start, 2)

    csv_logger.log_row(
        request_id=audio["request_id"],
        source=source,
        client_ip=client_ip,
        audio_filename=audio["filename"],
        text_filename=text_path.name,
        language=language,
        status="success",
        elapsed_seconds=elapsed,
        text=text,
    )

    return text_output.build_result(audio["request_id"], text, language, elapsed, audio["filename"], text_path.name)


# ---------------------------------------------------------------------------
# THE two integration points
# ---------------------------------------------------------------------------
async def process_upload(content: bytes, filename: str, language: str = DEFAULT_LANGUAGE, client_ip: str = "unknown") -> dict:
    """Full pipeline for one uploaded file. Raises ValueError (bad input) or RuntimeError (engine failure)."""
    try:
        audio = upload_input.receive_upload(filename, content)
    except ValueError as e:
        csv_logger.log_row(source="upload", client_ip=client_ip, language=language, status="rejected", error_message=str(e))
        raise
    return await _run_pipeline(audio, language, "upload", client_ip)


async def process_recording(session_id: str, filename: str, content: bytes, language: str = DEFAULT_LANGUAGE, client_ip: str = "unknown") -> dict:
    """Full pipeline for one finished live-recording session. Same error behaviour as process_upload."""
    try:
        audio = recorder_input.save_final_recording(session_id, filename, content)
    except ValueError as e:
        csv_logger.log_row(request_id=session_id, source="recording", client_ip=client_ip, language=language, status="rejected", error_message=str(e))
        raise
    return await _run_pipeline(audio, language, "recording", client_ip)


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(title="Speech-to-Text Service", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    engine_online = await speech_to_text.check_engine_online()
    return {"status": "ok", "engine_online": engine_online, "model": DEFAULT_MODEL}


@app.post("/api/transcribe")
async def transcribe(request: Request, file: UploadFile = File(...), language: str = Form(DEFAULT_LANGUAGE)):
    content = await file.read()
    client_ip = request.client.host if request.client else "unknown"
    try:
        result = await process_upload(content, file.filename, language, client_ip)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except RuntimeError as e:
        raise HTTPException(503, str(e))
    return JSONResponse(result)


@app.websocket("/ws/live")
async def live_recording(websocket: WebSocket):
    """
    Live preview only. The browser streams raw MediaRecorder chunks here
    while the user talks; this relays them to wlk and relays wlk's partial
    transcript messages back, so the UI can show text updating live.
    Nothing is saved from this connection - see /api/recording/finalize.
    """
    await websocket.accept()
    await recorder_input.relay_live_preview(websocket)


@app.post("/api/recording/finalize")
async def finalize_recording(
    request: Request,
    file: UploadFile = File(...),
    session_id: str = Form(...),
    language: str = Form(DEFAULT_LANGUAGE),
):
    """
    Called once the user presses pause/stop. Saves the complete recording
    and runs it through the same full-accuracy conversion as an upload.
    """
    content = await file.read()
    client_ip = request.client.host if request.client else "unknown"
    try:
        result = await process_recording(session_id, file.filename, content, language, client_ip)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except RuntimeError as e:
        raise HTTPException(503, str(e))
    return JSONResponse(result)


@app.get("/api/transcripts/{request_id}")
async def get_transcript(request_id: str):
    path = text_output.find_text(request_id)
    if not path:
        raise HTTPException(404, "Not found")
    return FileResponse(path)


@app.get("/api/audio/{request_id}")
async def get_audio(request_id: str):
    path = upload_input.find_audio(request_id)
    if not path:
        raise HTTPException(404, "Not found")
    return FileResponse(path)


# Serve the simple frontend (index.html, script.js, style.css) at "/"
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
