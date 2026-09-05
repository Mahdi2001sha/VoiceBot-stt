#!/bin/bash
# JOB: start wlk (the engine, from the base image), wait until it's
# genuinely ready (not just "started"), then start this project's own
# backend in the foreground so the container's lifecycle follows it.
set -e

echo "================================================"
echo "  Speech to Text - container starting"
echo "  Model: ${MODEL}"
echo "================================================"

echo "[1/3] Starting WhisperLiveKit engine (wlk)..."
wlk --host 0.0.0.0 --model "${MODEL}" --language "${LANGUAGE}" \
    --backend whisper --rest-timeout "${WLK_REST_TIMEOUT}" &
WLK_PID=$!

echo "[2/3] Waiting for the engine to finish loading (this can take a few minutes)..."
until python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)" >/dev/null 2>&1; do
    if ! kill -0 "$WLK_PID" 2>/dev/null; then
        echo "ERROR: wlk exited before becoming ready. Check the logs above."
        exit 1
    fi
    sleep 5
    echo "      still loading..."
done
echo "      Engine is ready."

echo "[3/3] Starting backend server..."
cd /project/backend
exec /opt/app-venv/bin/python run.py
