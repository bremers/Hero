"""Text-to-speech using Kokoro."""

import queue
import threading

import numpy as np
import sounddevice as sd
from kokoro import KPipeline
from loguru import logger

SAMPLE_RATE = 24000
AMP_WINDOW = 1200  # 50ms at 24kHz


class Speaker:
    def __init__(self, voice: str = "af_heart", speed: float = 1.0) -> None:
        logger.info("Loading Kokoro TTS...")
        self.pipeline = KPipeline(lang_code="a")
        self.voice = voice
        self.speed = speed

    def speak(self, text: str, state_queue: queue.Queue | None = None) -> None:
        logger.info(f"Speaking: {text}")

        # Collect all audio chunks
        chunks = []
        for result in self.pipeline(text, voice=self.voice, speed=self.speed):
            chunks.append(result.audio.numpy())

        if not chunks:
            return

        audio = np.concatenate(chunks)

        if state_queue is None:
            sd.play(audio, samplerate=SAMPLE_RATE)
            sd.wait()
            return

        # Stream with amplitude updates
        pos = 0
        done = threading.Event()

        def callback(outdata: np.ndarray, frames: int, time_info, status) -> None:
            nonlocal pos
            end = pos + frames
            if end <= len(audio):
                outdata[:, 0] = audio[pos:end]
            else:
                valid = len(audio) - pos
                outdata[:valid, 0] = audio[pos:]
                outdata[valid:, 0] = 0.0
                done.set()
                raise sd.CallbackStop
            pos = end

            rms = float(np.sqrt(np.mean(outdata[:, 0] ** 2)))
            state_queue.put(("amplitude", min(rms * 8, 1.0)))

        with sd.OutputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            blocksize=AMP_WINDOW,
            callback=callback,
        ):
            while not done.wait(timeout=0.1):
                pass

        state_queue.put(("amplitude", 0.0))
