"""Hello world TTS with Kokoro."""

import sounddevice as sd
from kokoro import KPipeline

pipeline = KPipeline(lang_code="a")

for audio in pipeline("Hello world!", voice="af_heart", speed=1.0):
    sd.play(audio.audio.numpy(), samplerate=24000)
    sd.wait()

print("Done.")
