# Hero

Local-first pipelined voice agent running entirely on-device (Apple Silicon).

## Pipeline

1. **Mic Capture** — `sounddevice` for real-time audio input
2. **VAD** — Silero VAD for voice activity detection
3. **ASR** — `faster-whisper` (CTranslate2) for speech-to-text
4. **LLM** — Ollama (local) for language understanding and response generation
5. **Memory** — ChromaDB (embedded) for short-term and long-term memory
6. **TTS** — Kokoro for text-to-speech output
7. **Vision** — MediaPipe for face/presence-gated activation

## Prerequisites

- macOS (Apple Silicon)
- Python 3.12+
- [Ollama](https://ollama.com) with a model pulled (e.g. `ollama pull llama3.2:1b`)
- PortAudio: `brew install portaudio`

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Usage

```bash
python -m hero
```
