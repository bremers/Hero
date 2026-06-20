"""Speech-to-text using faster-whisper."""

import numpy as np
from faster_whisper import WhisperModel
from loguru import logger


class Transcriber:
    def __init__(self, model_size: str = "base") -> None:
        logger.info(f"Loading Whisper model ({model_size})...")
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")

    def transcribe(self, audio: np.ndarray) -> str:
        segments, info = self.model.transcribe(audio, beam_size=5, language="en")
        text = " ".join(seg.text for seg in segments).strip()
        logger.info(f"Transcribed: {text}")
        return text
