"""Record 5 seconds of audio and transcribe with faster-whisper."""

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

SAMPLE_RATE = 16000
DURATION = 5

print(f"Recording {DURATION}s at {SAMPLE_RATE}Hz... Speak now!")
audio = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="float32")
sd.wait()
print("Recording complete.\n")

audio = audio.flatten()
print(f"Audio shape: {audio.shape}, min={audio.min():.4f}, max={audio.max():.4f}")

print("\nLoading Whisper model (base)... (first run downloads ~150MB)")
model = WhisperModel("base", device="cpu", compute_type="int8")

print("Transcribing...\n")
segments, info = model.transcribe(audio, beam_size=5)

print(f"Detected language: {info.language} (prob={info.language_probability:.2f})\n")
print("--- Transcription ---")
for segment in segments:
    print(f"[{segment.start:.1f}s - {segment.end:.1f}s] {segment.text}")
print("--- Done ---")
