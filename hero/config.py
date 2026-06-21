from pydantic import BaseModel


class Settings(BaseModel):
    sample_rate: int = 16000
    whisper_model: str = "base"
    ollama_model: str = "llama3.2:1b"
    ollama_host: str = "http://localhost:11434"
    vad_threshold: float = 0.5
    tts_voice: str = "af_heart"
    memory_path: str = "data/memories.json"
    chromadb_path: str = "data/chroma_db"
    camera_index: int = 1
    face_detection_confidence: float = 0.5
    facing_symmetry_threshold: float = 0.6
    widget_size: int = 200
