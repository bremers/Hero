# Hero — Claude Code Conventions

## Project overview
Hero is a local-first, pipelined voice agent for macOS (Apple Silicon).
Pipeline: Mic → VAD → ASR → LLM → Memory → TTS → Speakers.

## Tech stack
- Python 3.12, venv at `.venv/`
- ASR: faster-whisper (CTranslate2)
- VAD: silero-vad (PyTorch CPU)
- LLM: Ollama (HTTP client, server runs separately)
- Memory: ChromaDB (embedded, no server)
- TTS: Kokoro (ONNX Runtime)
- Audio I/O: sounddevice (PortAudio)
- Vision: mediapipe

## Commands
- Activate venv: `source .venv/bin/activate`
- Run: `python -m hero`
- Test: `pytest`
- Lint: `ruff check .`
- Format: `ruff format .`
- Install with dev deps: `pip install -e ".[dev]"`

## Conventions
- One pipeline stage per module in `hero/pipeline/`
- Use `loguru` for logging, not stdlib `logging`
- Use `pydantic` for config/settings
- Type hints required on all public functions
- Line length: 100 chars
- Ruff for linting and formatting

## M1 notes
- PyTorch CPU-only (no CUDA). `torch` default install on macOS ARM64 is correct.
- `onnxruntime` (not `onnxruntime-gpu`) for Kokoro TTS.
- PortAudio must be installed via `brew install portaudio` before `sounddevice`.
- `ffmpeg` must be available on PATH for faster-whisper.
