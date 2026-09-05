# Docker

This project uses a single `Dockerfile` in the project root that **places both the WhisperLiveKit engine and this project's backend/frontend in one image**. Instead of manually installing CUDA/torch, it uses the official WhisperLiveKit image (`ghcr.io/quentinfuxa/whisperlivekit`) as the base, which already has the correct CUDA/cuDNN/torch versions.

## Build the Image

From the project root (the same folder where `Dockerfile` is located):

```bash
docker build -t speech-to-text:latest .
```

## Run

### With GPU (Recommended - matches your RTX 4060)

Requires [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) on the Docker host system (on Windows: via WSL2 + Docker Desktop with GPU support enabled).

```bash
docker run --gpus all -p 8000:8000 -p 8080:8080 -v "%cd%\logs:/project/logs" speech-to-text:latest
```

(On Linux/macOS, use `$(pwd)` instead of `%cd%`.)

### Without GPU (CPU only - slower but works)

```bash
docker run -p 8000:8000 -p 8080:8080 -v "%cd%\logs:/project/logs" speech-to-text:latest
```

After startup (takes a few minutes for the model to load), go to: `http://localhost:8080`

### Change Model or Language Without Rebuilding the Image

```bash
docker run --gpus all -p 8000:8000 -p 8080:8080 \
  -e MODEL=large-v3-turbo \
  -e LANGUAGE=fa \
  -v "%cd%\logs:/project/logs" \
  speech-to-text:latest
```

### Configurable Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MODEL` | `large-v3` | Whisper model |
| `LANGUAGE` | `fa` | Default language |
| `WLK_REST_TIMEOUT` | `1800` | Engine timeout (seconds) |
| `MAX_CONCURRENT_TRANSCRIPTIONS` | `2` | Number of concurrent transcriptions |
| `TRANSCRIBE_TIMEOUT_SECONDS` | `1800` | Backend timeout (must be ≥ WLK_REST_TIMEOUT) |

### Preserving Logs Between Container Runs

The `logs/` folder (including Audio, Text, and log.csv) is mounted to a host folder with `-v` (the commands above do this) so it won't be lost when the container is removed.

## Upload to GitHub (GitHub Container Registry)

GitHub itself doesn't directly store image files, but **GitHub Container Registry (ghcr.io)** does exactly this and is linked to every GitHub account. Steps:

### 1) Create a Personal Access Token

On GitHub: Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token, with `write:packages` scope (and `read:packages`).

### 2) Login to ghcr.io

```bash
echo <YOUR_TOKEN> | docker login ghcr.io -u <YOUR_GITHUB_USERNAME> --password-stdin
```

### 3) Tag and Push

```bash
docker tag speech-to-text:latest ghcr.io/<YOUR_GITHUB_USERNAME>/speech-to-text:latest
docker push ghcr.io/<YOUR_GITHUB_USERNAME>/speech-to-text:latest
```

The image will then be visible at `https://github.com/<YOUR_GITHUB_USERNAME>?tab=packages`. To make it public: go to the package page → Package settings → Change visibility.

### 4) Run from the Pushed Image (on Any Other System)

```bash
docker pull ghcr.io/<YOUR_GITHUB_USERNAME>/speech-to-text:latest
docker run --gpus all -p 8000:8000 -p 8080:8080 -v "$(pwd)/logs:/project/logs" \
  ghcr.io/<YOUR_GITHUB_USERNAME>/speech-to-text:latest
```

## Important Notes

- **The image is large** (several gigabytes) because it includes CUDA + torch + Whisper models; this is normal for this type of project.
- The base image (`ghcr.io/quentinfuxa/whisperlivekit`) uses a "runtime" version of CUDA, not "devel"; so the same "Triton kernels" warning you've seen before (related to word timing calculation, not speech recognition itself) may still appear in Docker. This doesn't affect text accuracy, it's just a minor warning.
- If the target server doesn't have a GPU, run the command without `--gpus all`; it will be slower on CPU but will work correctly.