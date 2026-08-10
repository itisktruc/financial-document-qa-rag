import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Cấu hình ứng dụng và biến môi trường.
    # API Keys
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Vector Database Settings
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_COLLECTION: str = "financial_documents"

    # Embedding & Reranker Models
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-m3"
    RERANKER_MODEL_NAME: str = "BAAI/bge-reranker-v2-m3"

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )


settings = Settings()