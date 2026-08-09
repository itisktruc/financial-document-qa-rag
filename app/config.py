import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Keys
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Vector Database & Embedding
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_COLLECTION: str = "financial_documents"
    
    # Embedding & Reranker Models
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-m3"  # BGE-M3 cực mạnh cho tiếng Việt
    RERANKER_MODEL_NAME: str = "BAAI/bge-reranker-v2-m3"

    class Config:
        env_file = ".env"

settings = Settings()