# Speech to Text (v3)

Upload audio files or speak live with real-time text display, complete with storage and full logging.

## Folder Structure

```
speech-to-text/
├── start.bat              Run the entire project - default model can be changed here
├── requirements.txt
├── HELP.md                 Alternative commands (turbo model, transcription-only, etc.)
├── API_INTEGRATION.md      For integration into another project/chatbot + Docker
│
├── frontend/               Simple UI (upload + live recording)
│   ├── index.html
│   ├── style.css
│   └── script.js
│
├── backend/                Each file has exactly one responsibility
│   ├── main.py               Main hub - connects everything together + FastAPI server
│   ├── upload_input.py        Handles uploaded files
│   ├── recorder_input.py      Live preview (WebSocket) + save final recording
│   ├── speech_to_text.py      Convert audio to text (calls wlk)
│   ├── text_output.py          Save text + prepare output
│   ├── csv_logger.py            Log each request to log.csv
│   ├── config.py                 Settings (from .env)
│   ├── run.py                     Run the server
│   └── .env.example
│
└── logs/
    ├── Audio/                Each audio file: YYYYMMDDHHMMSS_ID.ext
    ├── Text/                  Text for each request: YYYYMMDDHHMMSS_ID.txt
    └── log.csv                  One row per request
```

## Running

Just double-click `start.bat`. It will:

1. Create a virtual environment (first time only)
2. Install packages from `requirements.txt`
3. Create `backend/.env` from `.env.example` (first time only)
4. Check if ffmpeg is installed (required for audio decoding by wlk)
5. Run `wlk` with the `large-v3` model (changeable at the top of `start.bat`)
6. Wait until the engine is actually ready (not just started)
7. Run this project's backend
8. Open the browser at `http://localhost:8080`

For alternative commands (different model, transcription-only, different port), see `HELP.md`.
For integration into another project or Docker, see `API_INTEGRATION.md`.

## Two Input Modes

- **File Upload**: Select an audio file, click the "Convert to Text" button, and the final result is displayed.
- **Live Recording**: Click the record button, text is displayed in real-time (preview); when you click the button again (pause/stop), the entire recording is saved and a final, more accurate conversion (on the complete file) is performed, which replaces the preview text.

Both paths go through the same `speech_to_text.py`, `text_output.py`, and `csv_logger.py` files, so storage and logging behavior is consistent.