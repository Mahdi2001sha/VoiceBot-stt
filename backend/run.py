"""
Starts the backend with settings sized for ~100 simultaneous client
connections. This does NOT mean 100 audio files get transcribed by the
whisper engine at the exact same instant (see MAX_CONCURRENT_TRANSCRIPTIONS
in .env) -- it means 100 people can upload / record / wait for their
result at the same time without the server rejecting or blocking them.
"""
import os

import uvicorn
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        limit_concurrency=100,
        backlog=128,
        log_level="info",
    )
