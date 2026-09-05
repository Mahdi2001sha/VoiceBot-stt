@echo off
setlocal enabledelayedexpansion

REM ================================================================
REM   Edit these two lines to change how the engine runs.
REM   MODEL must match a name wlk recognizes - run "wlk models" to see
REM   what's installed, or "wlk pull <name>" to download a new one.
REM   See HELP.md for ready-made command variations (turbo model,
REM   convert-without-saving, etc).
REM ================================================================
set "MODEL=large-v3"
set "WLK_REST_TIMEOUT=1800"

set "ROOT=%~dp0"
set "BACKEND=%ROOT%backend"
set "VENV=%BACKEND%\.venv"

echo ================================================
echo   Speech to Text - starting everything
echo   Model: %MODEL%
echo ================================================

REM ---- 1) Create a virtual environment if this is the first run ----
if not exist "%VENV%\Scripts\python.exe" (
    echo [1/6] Creating virtual environment...
    python -m venv "%VENV%"
)

REM ---- 2) Install/update dependencies from the root requirements.txt ----
echo [2/6] Installing dependencies...
call "%VENV%\Scripts\pip.exe" install -r "%ROOT%requirements.txt" -q

REM ---- 3) Make sure a .env file exists ----
if not exist "%BACKEND%\.env" (
    copy "%BACKEND%\.env.example" "%BACKEND%\.env" >nul
    echo       Created backend\.env from .env.example - edit it if you need to.
)

REM ---- 4) Check ffmpeg is installed - wlk needs it to decode audio ----
where ffmpeg >nul 2>nul
if errorlevel 1 (
    echo.
    echo WARNING: ffmpeg was not found on your PATH.
    echo WhisperLiveKit uses ffmpeg to decode uploaded/recorded audio, and
    echo transcription will fail with a 500 error without it. Install it from:
    echo   https://www.gyan.dev/ffmpeg/builds/
    echo and add its "bin" folder to your system PATH, then re-run start.bat.
    echo.
    timeout /t 5 /nobreak >nul
)

REM ---- 5) Start WhisperLiveKit (wlk) in its own window ----
echo [3/6] Starting WhisperLiveKit engine (wlk) with model %MODEL%...
start "WhisperLiveKit (wlk)" cmd /k "wlk --model %MODEL% --language fa --backend whisper --rest-timeout %WLK_REST_TIMEOUT%"

REM ---- 6) Wait until wlk is ACTUALLY ready, not just "started" ----
REM   large-v3 on CPU can take a couple of minutes to load into memory.
REM   Sending requests before it's ready gets a 503 from wlk itself.
echo [4/6] Waiting for the speech engine to finish loading...
echo       (this can take a few minutes on CPU - please wait)
set "WLK_READY=0"
for /l %%i in (1,1,60) do (
    curl -s -o nul -w "%%{http_code}" http://127.0.0.1:8000/health > "%TEMP%\wlk_status.txt" 2>nul
    set /p WLK_CODE=<"%TEMP%\wlk_status.txt"
    if "!WLK_CODE!"=="200" (
        set "WLK_READY=1"
        goto :wlk_ready
    )
    timeout /t 5 /nobreak >nul
    echo       still loading... (%%i0s elapsed)
)
:wlk_ready

if "%WLK_READY%"=="1" (
    echo       Engine is ready.
) else (
    echo       WARNING: engine did not respond after 5 minutes.
    echo       Check the "WhisperLiveKit (wlk)" window for errors.
    echo       Continuing anyway - you can retry once it finishes loading.
)

REM ---- 7) Start this project's backend in its own window ----
echo [5/6] Starting backend server...
start "Speech-to-Text Backend" cmd /k ""%VENV%\Scripts\python.exe" "%BACKEND%\run.py""

REM ---- 8) Open the app in the browser ----
echo [6/6] Opening the app...
timeout /t 3 /nobreak >nul
start "" http://localhost:8080

echo.
echo Two windows are now running:
echo   - WhisperLiveKit (wlk)      : the speech engine
echo   - Speech-to-Text Backend    : this project's server
echo Close either window to stop that part. This window can be closed.
echo.
pause >nul
