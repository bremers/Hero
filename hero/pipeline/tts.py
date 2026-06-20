"""Text-to-speech using Kokoro."""

import sounddevice as sd
from kokoro import KPipeline
from loguru import logger


class Speaker:
    def __init__(self, voice: str = "af_heart", speed: float = 1.0) -> None:
        logger.info("Loading Kokoro TTS...")
        self.pipeline = KPipeline(lang_code="a")
        self.voice = voice
        self.speed = speed

    def speak(self, text: str) -> None:
        logger.info(f"Speaking: {text}")
        for audio in self.pipeline(text, voice=self.voice, speed=self.speed):
            sd.play(audio.audio.numpy(), samplerate=24000)
            sd.wait()
