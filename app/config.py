from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "financial_rag_corrected")
    
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY: str | None = os.getenv("QDRANT_API_KEY", None)
    QDRANT_COLLECTION: str = os.getenv("QDRANT_COLLECTION", "financial_chunks")
    
    GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY", None)
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY", None)
    
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-m3")
    RERANKER_MODEL_NAME: str = os.getenv("RERANKER_MODEL_NAME", "BAAI/bge-reranker-v2-m3")

settings = Settings()

MONGO_URI = settings.MONGO_URI
QDRANT_URL = settings.QDRANT_URL
QDRANT_API_KEY = settings.QDRANT_API_KEY