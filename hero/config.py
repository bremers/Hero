from pydantic import BaseModel


class Settings(BaseModel):
    sample_rate: int = 16000
    whisper_model: str = "base"
    ollama_model: str = "llama3.2:1b"
    ollama_host: str = "http://localhost:11434"
    vad_threshold: float = 0.5
    tts_voice: str = "af_heart"
    chromadb_path: str = "data/chroma_db"
