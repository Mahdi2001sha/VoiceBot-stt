# Command Guide (HELP)

This file shows several different ways to run the project. All of them can be done by just changing the same single `wlk` command line in `start.bat` (or running it manually) — none require changing the project code.

## Default Execution (what `start.bat` runs by itself)

```
wlk --model large-v3 --language fa --backend whisper --rest-timeout 1800
```

## Using a Different Model (e.g., large-v3-turbo)

Just change the `MODEL` value at the top of `start.bat`:

```
set "MODEL=large-v3-turbo"
```

Or directly in the terminal:

```
wlk --model large-v3-turbo --language fa --backend whisper --rest-timeout 1800
```

See installed models with:

```
wlk models
```

And to download a new model:

```
wlk pull large-v3-turbo
```

## Transcription Only, Without Saving to the Project

If you just want to quickly test a file and don't want it to go into the project (and CSV logs or `logs/Audio` and `logs/Text` folders), talk directly to `wlk` itself and bypass the project backend:

```
curl -X POST http://127.0.0.1:8000/v1/audio/transcriptions -F "file=@C:\path\to\audio.wav" -F "language=fa"
```

This doesn't save any files in this project and doesn't log anything to `log.csv`, because it doesn't go through this project's backend at all.

## Running Each Part Independently (without start.bat)

If you don't want to use `start.bat`:

```
# Terminal 1 - Engine
wlk --model large-v3 --language fa --backend whisper --rest-timeout 1800

# Terminal 2 - This project's backend
cd backend
.venv\Scripts\python.exe run.py
```

## Helper Settings for Better Accuracy/Speed (Optional)

```
wlk --model large-v3 --language fa --backend whisper --rest-timeout 1800 --beams 3 --never-fire --backend-policy localagreement
```

- `--beams 3` increases accuracy, but slows things down a bit (default is 1 = greedy).
- `--never-fire` prevents words from being cut off in the middle of recording.
- `--backend-policy localagreement` sometimes gives more coherent grammar for complete files (not live streaming).

If speed is more important and you just want ffmpeg + a faster model:

```
wlk --model medium --language fa --backend whisper --rest-timeout 1800
```

## Different Port or Host for the Engine

```
wlk --model large-v3 --language fa --backend whisper --host 0.0.0.0 --port 9000
```

If you change the engine port, you should also update `backend\.env`:

```
WHISPER_API_URL=http://127.0.0.1:9000/v1/audio/transcriptions
WHISPER_BASE_URL=http://127.0.0.1:9000
WHISPER_WS_URL=ws://127.0.0.1:9000/asr
```

## ffmpeg Not Installed

If the engine errors out with a file-not-found error (`FileNotFoundError: [WinError 2]`), it means ffmpeg isn't installed or isn't in your PATH. Install it from here:
https://www.gyan.dev/ffmpeg/builds/
and add the `bin` folder inside it to your system PATH, then open a new terminal.