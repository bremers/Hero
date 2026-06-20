"""LLM inference via Ollama."""

import ollama
from loguru import logger

SYSTEM_PROMPT = (
    "You are Hero, a friendly and curious companion robot. "
    "You speak in short, warm sentences. You are cheerful and helpful. "
    "Keep responses to 1-2 sentences so they sound natural when spoken aloud."
)


class Companion:
    def __init__(self, model: str = "llama3.2:1b", host: str = "http://localhost:11434") -> None:
        self.model = model
        self.client = ollama.Client(host=host)
        self.history: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]

    def respond(self, user_text: str) -> str:
        self.history.append({"role": "user", "content": user_text})
        response = self.client.chat(model=self.model, messages=self.history)
        reply = response.message.content
        self.history.append({"role": "assistant", "content": reply})
        logger.info(f"LLM reply: {reply}")
        return reply
