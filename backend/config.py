from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional
import torch


class Settings(BaseSettings):
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    MODEL_DIR: Path = BASE_DIR / "models"
    CHROMA_DIR: Path = BASE_DIR / "data" / "chroma_db"
    UPLOAD_DIR: Path = BASE_DIR / "data" / "uploads"
    PAPERS_DIR: Path = BASE_DIR / "data" / "papers"

    DEVICE: str = "mps" if torch.backends.mps.is_available() else "cpu"
    USE_FP16: bool = torch.backends.mps.is_available()

    FAKE_THRESHOLD: float = 0.5
    HIGH_CONFIDENCE_THRESHOLD: float = 0.85
    LOW_CONFIDENCE_THRESHOLD: float = 0.3

    SPATIAL_MODEL: str = "facebook/dinov2-base"

    MAX_FRAMES: int = 64
    FRAME_SAMPLE_RATE: int = 4
    TARGET_FACE_SIZE: tuple = (224, 224)

    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    CHROMA_COLLECTION: str = "ankara_forensic_papers"
    RAG_TOP_K: int = 5
    LLM_PROVIDER: str = "ollama"
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    MAX_UPLOAD_SIZE_MB: int = 500
    CORS_ORIGINS: list = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

for d in [settings.MODEL_DIR, settings.CHROMA_DIR, settings.UPLOAD_DIR, settings.PAPERS_DIR]:
    d.mkdir(parents=True, exist_ok=True)
