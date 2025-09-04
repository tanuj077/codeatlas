from dotenv import load_dotenv
from pydantic import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "CodeAtlas"

    # Embedding backend (required from .env)
    CODEATLAS_EMBEDDER: str

    EMBEDDING_MODEL_NAME: str  # No default; must be set in .env

    # OpenAI config (optional)
    OPENAI_API_KEY: str = None

    # LLM backend (required from .env)
    CODEATLAS_CHAT_BACKEND: str

    LLM_MODEL_NAME: str  # No default; must be set in .env

    # Repository root (required from .env)
    CODEATLAS_REPO_ROOT: str

    VECTOR_STORE_DIR: str = "vector_store"  # Optional default kept

    class Config:
        env_file = ".env"
        extra = "ignore"  # Allow extra env vars safely

    def __post_init__(self):
        # Validate required fields
        if not self.CODEATLAS_EMBEDDER:
            raise ValueError("CODEATLAS_EMBEDDER must be set in .env")
        if not self.EMBEDDING_MODEL_NAME:
            raise ValueError("EMBEDDING_MODEL_NAME must be set in .env")
        if not self.CODEATLAS_CHAT_BACKEND:
            raise ValueError("CODEATLAS_CHAT_BACKEND must be set in .env")
        if not self.LLM_MODEL_NAME:
            raise ValueError("LLM_MODEL_NAME must be set in .env")
        if not self.CODEATLAS_REPO_ROOT:
            raise ValueError("CODEATLAS_REPO_ROOT must be set in .env")

    @property
    def EMBEDDER_BACKEND(self):
        return self.CODEATLAS_EMBEDDER

    @property
    def CHAT_BACKEND(self):
        return self.CODEATLAS_CHAT_BACKEND

    @property
    def USE_OPENAI(self):
        return self.CODEATLAS_CHAT_BACKEND.lower() == "openai"

    @property
    def REPO_ROOT(self):
        return self.CODEATLAS_REPO_ROOT

settings = Settings()
