import os
from pydantic_settings import BaseSettings



class Settings(BaseSettings):
    # API Keys
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    #MONGO_URI: str = os.getenv("MONGO_URI", "")
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://admin:changeme@mongodb:27017")
    MONGO_DB: str = os.getenv("MONGO_DB", "financial_rag")

    QDRANT_URL: str = os.getenv("QDRANT_URL", "")
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")   

    #QDRANT_URL = os.getenv("QDRANT_URL")
    #QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    
    # Vector Database & Embedding
    #QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")

    #MONGO_DB: str = os.getenv("MONGO_DB", "financial_rag")

    # Embedding & Reranker Models
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-m3"  # BGE-M3 cực mạnh cho tiếng Việt
    RERANKER_MODEL_NAME: str = "BAAI/bge-reranker-base"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()