"""Test that long-term memory persists across sessions."""

import json
from pathlib import Path

from hero.pipeline.llm import Companion
from hero.pipeline.memory import Memory

TEST_PATH = "data/test_memories.json"


def cleanup() -> None:
    Path(TEST_PATH).unlink(missing_ok=True)


def test_remember_and_recall() -> None:
    cleanup()

    # Session 1: tell Hero our name
    memory = Memory(path=TEST_PATH)
    companion = Companion(memory=memory)
    reply = companion.respond("My name is Alexandra.")
    print(f"Session 1 reply: {reply}")

    # Check something was remembered
    saved = json.loads(Path(TEST_PATH).read_text())
    print(f"Saved memories: {json.dumps(saved, indent=2)}")

    # Session 2: new companion, same memory file — ask for the name
    memory2 = Memory(path=TEST_PATH)
    companion2 = Companion(memory=memory2)
    reply2 = companion2.respond("What's my name?")
    print(f"Session 2 reply: {reply2}")

    cleanup()


if __name__ == "__main__":
    test_remember_and_recall()
