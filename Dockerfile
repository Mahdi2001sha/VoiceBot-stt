# ============================================================================
# Single image containing BOTH the WhisperLiveKit engine AND this project's
# backend + frontend, so `docker run` on this one image gives you the whole
# app. Built on top of WhisperLiveKit's own official prebuilt image
# (ghcr.io/quentinfuxa/whisperlivekit) instead of reinstalling CUDA/torch
# ourselves - that image already has the right CUDA/cuDNN/torch versions
# matched to `wlk`, which is the hard part to get right by hand.
#
# GPU support: this base image is CUDA-based. To actually use your GPU
# inside the container you need the NVIDIA Container Toolkit installed on
# the host and to run with `--gpus all` (see DOCKER.md). Without it, the
# engine still runs, just falls back to CPU (slower, but works).
# ============================================================================
FROM ghcr.io/quentinfuxa/whisperlivekit:latest

# The base image manages its own Python environment with `uv`, not plain
# pip, so we don't try to guess its internals. Instead we create a totally
# separate venv just for our own packages, using the system python3 that
# must exist underneath any venv - fully independent of however wlk's own
# environment is set up.
RUN python3 -m venv /opt/app-venv && \
    /opt/app-venv/bin/pip install --no-cache-dir \
        fastapi==0.115.0 \
        "uvicorn[standard]==0.30.6" \
        httpx==0.27.2 \
        websockets==13.1 \
        python-multipart==0.0.9 \
        python-dotenv==1.0.1

# Keep our project separate from the base image's /app (which belongs to wlk)
WORKDIR /project
COPY backend/ ./backend/
COPY frontend/ ./frontend/
RUN mkdir -p ./logs/Audio ./logs/Text

# Sensible defaults - override any of these with `docker run -e NAME=value`
ENV MODEL=large-v3
ENV LANGUAGE=fa
ENV WLK_REST_TIMEOUT=1800
ENV HOST=0.0.0.0
ENV PORT=8080
ENV WHISPER_API_URL=http://127.0.0.1:8000/v1/audio/transcriptions
ENV WHISPER_BASE_URL=http://127.0.0.1:8000
ENV WHISPER_WS_URL=ws://127.0.0.1:8000/asr

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# 8000 = wlk (engine), 8080 = this project's web UI + API
EXPOSE 8000 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=180s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/health')" || exit 1

ENTRYPOINT ["/docker-entrypoint.sh"]
