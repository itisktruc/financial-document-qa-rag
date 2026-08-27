from dotenv import load_dotenv
import os

load_dotenv()

# Mongo
MONGO_URI_LOCAL = os.getenv("MONGO_URI_LOCAL", "mongodb://localhost:27017")
MONGO_URI_CLOUD = os.getenv("MONGO_URI_CLOUD")
MONGO_DB_DOCUMENTS = os.getenv("MONGO_DB_DOCUMENTS", "financial_rag")
MONGO_DB_CHUNKS = os.getenv("MONGO_DB_CHUNKS", "financial_rag_corrected")
DOCUMENTS_COLLECTION = os.getenv("DOCUMENTS_COLLECTION", "documents_2025")

# Qdrant
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "financial_chunks")
VECTOR_SIZE = 1024

# Embedding
EMBEDDING_MODEL_ID = os.getenv("EMBEDDING_MODEL_ID", "BAAI/bge-m3")
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "12"))
EMBEDDING_MAX_LENGTH = int(os.getenv("EMBEDDING_MAX_LENGTH", "8192"))
EMBEDDING_USE_FP16 = os.getenv("EMBEDDING_USE_FP16", "auto")