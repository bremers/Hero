"""LLM inference via Ollama."""

import ollama
from loguru import logger

from hero.pipeline.memory import Memory

SYSTEM_PROMPT = """\
You are Hero, a friendly and curious companion robot.
You speak in short, warm sentences. Keep responses to 1-2 sentences.

IMPORTANT RULE: When the user shares a personal fact (name, preference, routine, \
favorite thing), you MUST add a <remember> tag at the end of your reply.

Examples:
User: "I'm Alexandra"
You: "Nice to meet you, Alexandra! <remember>User's name is Alexandra</remember>"

User: "I love coffee"
You: "Me too — well, if I could drink it! <remember>User loves coffee</remember>"

User: "What time is it?"
You: "I'm not sure, but I hope you're having a great day!"

Only use <remember> for NEW personal facts. Never repeat already-known facts."""


class Companion:
    def __init__(
        self,
        model: str = "llama3.2:1b",
        host: str = "http://localhost:11434",
        memory: Memory | None = None,
    ) -> None:
        self.model = model
        self.client = ollama.Client(host=host)
        self.memory = memory or Memory()
        self._build_system_prompt()

    def _build_system_prompt(self) -> None:
        prompt = SYSTEM_PROMPT + self.memory.to_prompt_block()
        self.history: list[dict[str, str]] = [{"role": "system", "content": prompt}]

    def respond(self, user_text: str) -> str:
        self.history.append({"role": "user", "content": user_text})
        response = self.client.chat(model=self.model, messages=self.history)
        raw_reply = response.message.content
        reply = self.memory.extract_and_store(raw_reply)
        self.history.append({"role": "assistant", "content": reply})
        logger.info(f"LLM reply: {reply}")
        return reply
