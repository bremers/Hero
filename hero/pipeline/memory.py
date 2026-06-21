"""Long-term memory backed by a local JSON file."""

import json
import re
from datetime import UTC, datetime
from pathlib import Path

from loguru import logger

REMEMBER_PATTERN = re.compile(
    r"<\s*remember[\s=:>]*(.*?)<\s*/?\s*remember\s*>", re.DOTALL | re.IGNORECASE
)
# Catch any leftover tag-like fragments the primary pattern missed
REMEMBER_CLEANUP = re.compile(r"<\s*/?\s*remember[^>]*>", re.IGNORECASE)


class Memory:
    def __init__(self, path: str = "data/memories.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.facts: list[dict[str, str]] = self._load()
        logger.info(f"Loaded {len(self.facts)} memories from {self.path}")

    def _load(self) -> list[dict[str, str]]:
        if not self.path.exists():
            return []
        try:
            return json.loads(self.path.read_text())
        except (json.JSONDecodeError, OSError):
            logger.warning(f"Could not read {self.path}, starting fresh")
            return []

    def _save(self) -> None:
        self.path.write_text(json.dumps(self.facts, indent=2))

    def extract_and_store(self, llm_response: str) -> str:
        """Parse <remember> tags from LLM output, store facts, return cleaned response."""
        matches = REMEMBER_PATTERN.findall(llm_response)
        for fact in matches:
            fact = fact.strip()
            if fact and not any(m["fact"] == fact for m in self.facts):
                self.facts.append(
                    {
                        "fact": fact,
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                )
                logger.info(f"Remembered: {fact}")
        if matches:
            self._save()
        cleaned = REMEMBER_PATTERN.sub("", llm_response)
        cleaned = REMEMBER_CLEANUP.sub("", cleaned)
        return cleaned.strip()

    def to_prompt_block(self) -> str:
        """Format all memories for injection into the system prompt."""
        if not self.facts:
            return ""
        lines = "\n".join(f"- {m['fact']}" for m in self.facts)
        return f"\n\nWhat you know about the user:\n{lines}"
