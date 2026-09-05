# Integrating This Project into Another Project/Chatbot (API + Docker)

This project provides two ways to be used in another project (e.g., an LLM/chatbot): via HTTP API, or by directly importing Python functions (if your other project is also in Python).

Default server at: `http://<server-ip>:8080`

## 1) Via HTTP API

### Upload a Complete File

```bash
curl -X POST http://<server-ip>:8080/api/transcribe \
  -F "file=@voice.wav" \
  -F "language=fa"
```

Response:

```json
{
  "request_id": "a1b2c3d4",
  "text": "Transcribed text...",
  "language": "fa",
  "elapsed_seconds": 3.47,
  "audio_file": "20260813120000_a1b2c3d4.wav",
  "text_file": "20260813120000_a1b2c3d4.txt"
}
```

### Live Recording (WebSocket Preview + finalize)

```
ws://<server-ip>:8080/ws/live?session_id=<custom-identifier>
```

- Send raw audio bytes (MediaRecorder chunks in webm/opus format) to this connection.
- The JSON text messages returned show real-time (preview) text. This is just a preview and is not saved.

When recording is complete, send the full recorded file with the same `session_id` to this endpoint to save it and get the final (more accurate than live preview) text:

```bash
curl -X POST http://<server-ip>:8080/api/recording/finalize \
  -F "file=@recording.webm" \
  -F "session_id=a1b2c3d4" \
  -F "language=fa"
```

The response has exactly the same format as `/api/transcribe`.

### Other Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | `{status, engine_online, model}` |
| GET | `/api/transcripts/{request_id}` | Download saved text (.txt) |
| GET | `/api/audio/{request_id}` | Download saved audio file |

### Python Example (requests)

```python
import requests

with open("voice.wav", "rb") as f:
    r = requests.post(
        "http://<server-ip>:8080/api/transcribe",
        files={"file": f},
        data={"language": "fa"},
    )
print(r.json()["text"])
```

## 2) Direct Python Import (No HTTP, Fastest if Your Project is Also Python)

The `backend/main.py` file is designed specifically to be importable:

```python
import sys
sys.path.insert(0, "path/to/speech-to-text/backend")

from main import process_upload

result = await process_upload(audio_bytes, "voice.wav", language="fa")
print(result["text"])
```

This function handles validation, audio file saving, calling the engine, text saving, and CSV logging all by itself — no server needs to be running, only the `wlk` process must be running.

## 3) Docker (Optional)

This backend can be placed in a separate container. Note: **wlk must be run separately** — either on the host itself, or in another container — because this project only connects to wlk via HTTP/WebSocket and doesn't include its code.

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY logs/ ./logs/

WORKDIR /app/backend
ENV WHISPER_API_URL=http://host.docker.internal:8000/v1/audio/transcriptions
ENV WHISPER_BASE_URL=http://host.docker.internal:8000
ENV WHISPER_WS_URL=ws://host.docker.internal:8000/asr

EXPOSE 8080
CMD ["python", "run.py"]
```

Build and run:

```bash
docker build -f backend/Dockerfile -t stt-backend .
docker run -p 8080:8080 stt-backend
```

`host.docker.internal` on Docker Windows/Mac points to the host (where wlk is running). On Linux, you need to either use `--add-host=host.docker.internal:host-gateway` or run wlk in a separate container (or with `network_mode: host`).