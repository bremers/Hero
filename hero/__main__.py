"""Hero voice agent — 5-turn conversation loop with addressee detection."""

import time

from loguru import logger

from hero.config import Settings
from hero.pipeline.asr import Transcriber
from hero.pipeline.llm import Companion
from hero.pipeline.memory import Memory
from hero.pipeline.mic import record_utterance
from hero.pipeline.tts import Speaker
from hero.vision.presence import PresenceDetector

MAX_TURNS = 5


def main() -> None:
    settings = Settings()
    logger.info("Loading models...")

    transcriber = Transcriber(model_size=settings.whisper_model)
    memory = Memory(path=settings.memory_path)
    companion = Companion(model=settings.ollama_model, host=settings.ollama_host, memory=memory)
    speaker = Speaker(voice=settings.tts_voice)

    with PresenceDetector(
        camera_index=settings.camera_index,
        detection_confidence=settings.face_detection_confidence,
        symmetry_threshold=settings.facing_symmetry_threshold,
    ) as presence:
        logger.info("Hero is ready. Look at the camera and speak!\n")

        try:
            engaged = False
            for turn in range(1, MAX_TURNS + 1):
                print(f"\n--- Turn {turn}/{MAX_TURNS} ---")

                if not engaged:
                    while not presence.is_addressed:
                        time.sleep(0.2)
                    engaged = True
                    logger.info("Addressee engaged — starting conversation")

                logger.info(f"[Turn {turn}] Addressee: {'facing' if presence.is_addressed else 'not facing'}")

                audio = record_utterance(vad_threshold=settings.vad_threshold)
                if audio is None:
                    print("No speech detected, skipping.")
                    continue

                text = transcriber.transcribe(audio)
                if not text:
                    print("Could not transcribe, skipping.")
                    continue

                print(f"You: {text}")

                reply = companion.respond(text)
                print(f"Hero: {reply}")

                speaker.speak(reply)
        except KeyboardInterrupt:
            print("\n\nInterrupted — goodbye!")

    print("\n--- Conversation complete! ---")


if __name__ == "__main__":
    main()
