"""Mic capture stage with VAD-triggered start/stop."""

import threading
import time

import numpy as np
import sounddevice as sd
import torch
from loguru import logger
from silero_vad import load_silero_vad

CHUNK_SAMPLES = 512
SAMPLE_RATE = 16000
CHUNK_DURATION = CHUNK_SAMPLES / SAMPLE_RATE


def record_utterance(
    vad_threshold: float = 0.5,
    silence_limit: float = 1.0,
    max_duration: float = 15.0,
    pre_speech_buffer: float = 0.3,
    cooldown: float = 0.5,
) -> np.ndarray | None:
    """Block until speech is detected, then record until silence. Returns float32 mono audio."""
    vad = load_silero_vad()
    vad.reset_states()

    # Discard mic input briefly so we don't pick up TTS playback
    time.sleep(cooldown)

    chunks: list[np.ndarray] = []
    pre_chunks: list[np.ndarray] = []
    max_pre = int(pre_speech_buffer / CHUNK_DURATION)
    speaking = False
    silent_chunks = 0
    silent_limit = int(silence_limit / CHUNK_DURATION)
    max_chunks = int(max_duration / CHUNK_DURATION)
    done = threading.Event()

    logger.info("Listening... (speak to start)")

    def callback(indata: np.ndarray, frames: int, time_info, status) -> None:
        nonlocal speaking, silent_chunks
        if status:
            logger.warning(f"Audio status: {status}")

        chunk = indata[:, 0].copy()
        tensor = torch.from_numpy(chunk)
        prob = vad(tensor, SAMPLE_RATE).item()

        if not speaking:
            pre_chunks.append(chunk)
            if len(pre_chunks) > max_pre:
                pre_chunks.pop(0)
            if prob >= vad_threshold:
                speaking = True
                silent_chunks = 0
                chunks.extend(pre_chunks)
                chunks.append(chunk)
                logger.info("Speech detected")
        else:
            chunks.append(chunk)
            if prob < vad_threshold:
                silent_chunks += 1
                if silent_chunks >= silent_limit:
                    done.set()
                    raise sd.CallbackStop
            else:
                silent_chunks = 0

            if len(chunks) >= max_chunks:
                done.set()
                raise sd.CallbackStop

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        blocksize=CHUNK_SAMPLES,
        callback=callback,
    ):
        # Poll with short timeout so Ctrl+C can interrupt
        while not done.wait(timeout=0.1):
            pass

    if not chunks:
        return None

    audio = np.concatenate(chunks)
    logger.info(f"Captured {len(audio) / SAMPLE_RATE:.1f}s of audio")
    return audio
