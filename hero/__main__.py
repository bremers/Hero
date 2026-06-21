"""Hero voice agent — 5-turn conversation loop."""

from loguru import logger

from hero.config import Settings
from hero.pipeline.asr import Transcriber
from hero.pipeline.llm import Companion
from hero.pipeline.memory import Memory
from hero.pipeline.mic import record_utterance
from hero.pipeline.tts import Speaker

MAX_TURNS = 5


def main() -> None:
    settings = Settings()
    logger.info("Loading models...")

    transcriber = Transcriber(model_size=settings.whisper_model)
    memory = Memory(path=settings.memory_path)
    companion = Companion(model=settings.ollama_model, host=settings.ollama_host, memory=memory)
    speaker = Speaker(voice=settings.tts_voice)

    logger.info("Hero is ready. Speak to begin!\n")

    try:
        for turn in range(1, MAX_TURNS + 1):
            print(f"\n--- Turn {turn}/{MAX_TURNS} ---")

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
