"""Hero voice agent — conversation loop with widget and gesture detection."""

import queue
import re
import threading
import time

from loguru import logger

from hero.config import Settings
from hero.pipeline.asr import Transcriber
from hero.pipeline.llm import Companion
from hero.pipeline.memory import Memory
from hero.pipeline.mic import record_utterance
from hero.pipeline.tts import Speaker
from hero.ui.widget import HeroWidget
from hero.vision.presence import PresenceDetector

MAX_TURNS = 5
GOODBYE_PATTERN = re.compile(r"\b(goodbye|bye)\b", re.IGNORECASE)


def _say_goodbye(
    speaker: Speaker,
    state_queue: queue.Queue,
) -> None:
    state_queue.put("speaking")
    speaker.speak("Goodbye! It was nice chatting with you!", state_queue)
    state_queue.put("goodbye")


def _wave_monitor(
    presence: PresenceDetector,
    cancel: threading.Event,
    stop: threading.Event,
) -> None:
    """Background thread that checks for wave gestures and cancels recording."""
    while not stop.is_set():
        if presence.detected_wave:
            logger.info("Wave detected — triggering goodbye")
            cancel.set()
            return
        stop.wait(0.2)


def _pipeline(
    settings: Settings,
    state_queue: queue.Queue,
    presence: PresenceDetector,
) -> None:
    logger.info("Loading models...")

    transcriber = Transcriber(model_size=settings.whisper_model)
    memory = Memory(path=settings.memory_path)
    companion = Companion(model=settings.ollama_model, host=settings.ollama_host, memory=memory)
    speaker = Speaker(voice=settings.tts_voice)

    logger.info("Hero is ready. Look at the camera and speak!\n")

    cancel = threading.Event()
    stop_monitor = threading.Event()

    monitor = threading.Thread(
        target=_wave_monitor,
        args=(presence, cancel, stop_monitor),
        daemon=True,
    )
    monitor.start()

    engaged = False
    try:
        for turn in range(1, MAX_TURNS + 1):
            if cancel.is_set():
                _say_goodbye(speaker, state_queue)
                return

            print(f"\n--- Turn {turn}/{MAX_TURNS} ---")

            if not engaged:
                while not presence.is_addressed:
                    if cancel.is_set():
                        _say_goodbye(speaker, state_queue)
                        return
                    time.sleep(0.2)
                engaged = True
                logger.info("Addressee engaged — starting conversation")

            state_queue.put("listening")
            logger.info(
                f"[Turn {turn}] Addressee: {'facing' if presence.is_addressed else 'not facing'}"
            )

            audio = record_utterance(vad_threshold=settings.vad_threshold, cancel=cancel)

            if cancel.is_set():
                _say_goodbye(speaker, state_queue)
                return

            if audio is None:
                state_queue.put("idle")
                print("No speech detected, skipping.")
                continue

            text = transcriber.transcribe(audio)
            if not text:
                state_queue.put("idle")
                print("Could not transcribe, skipping.")
                continue

            print(f"You: {text}")

            if GOODBYE_PATTERN.search(text):
                logger.info("Goodbye detected in speech")
                state_queue.put("speaking")
                reply = companion.respond(text)
                print(f"Hero: {reply}")
                speaker.speak(reply, state_queue)
                state_queue.put("goodbye")
                return

            reply = companion.respond(text)
            print(f"Hero: {reply}")

            state_queue.put("speaking")
            speaker.speak(reply, state_queue)
            state_queue.put("idle")

    except KeyboardInterrupt:
        state_queue.put("goodbye")
        print("\n\nInterrupted — goodbye!")
        return
    finally:
        stop_monitor.set()

    state_queue.put("goodbye")
    print("\n--- Conversation complete! ---")


def main() -> None:
    settings = Settings()
    state_queue: queue.Queue = queue.Queue()

    with PresenceDetector(
        camera_index=settings.camera_index,
        detection_confidence=settings.face_detection_confidence,
        symmetry_threshold=settings.facing_symmetry_threshold,
    ) as presence:
        pipeline_thread = threading.Thread(
            target=_pipeline,
            args=(settings, state_queue, presence),
            daemon=True,
        )
        pipeline_thread.start()

        widget = HeroWidget(state_queue)
        widget.run()


if __name__ == "__main__":
    main()
