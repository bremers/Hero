"""Hello world Ollama call."""

import ollama

response = ollama.chat(
    model="llama3.2:1b",
    messages=[{"role": "user", "content": "Tell me a fact about birds."}],
)

print(response.message.content)
