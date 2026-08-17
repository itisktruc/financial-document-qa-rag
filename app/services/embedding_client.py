from typing import Dict, Any, List
from app.config import settings
import logging

logger = logging.getLogger(__name__)

_model = None

def _get_embedding_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL_NAME}")
            _model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        except Exception as e:
            logger.warning(f"Could not load SentenceTransformer ({e}). Trying FlagEmbedding...")
            try:
                from FlagEmbedding import BGEM3FlagModel
                _model = BGEM3FlagModel(settings.EMBEDDING_MODEL_NAME, use_fp16=False)
            except Exception as e2:
                logger.error(f"Failed to load FlagEmbedding ({e2}). Will use dummy fallback embedding.")
                _model = "dummy"
    return _model

def embed_query(query: str, return_sparse: bool = False) -> Dict[str, Any]:
    """Tạo vector embedding cho câu hỏi tìm kiếm."""
    model = _get_embedding_model()
    if model == "dummy" or model is None:
        # Fallback dummy 1024-dim vector for testing/offline mode
        return {"dense": [0.0] * 1024}
    
    try:
        if hasattr(model, "encode"):
            res = model.encode(query)
            if isinstance(res, dict) and "dense_vecs" in res:
                vec = res["dense_vecs"].tolist()
            elif hasattr(res, "tolist"):
                vec = res.tolist()
            elif isinstance(res, list):
                vec = res
            else:
                vec = list(res)
            return {"dense": vec}
    except Exception as e:
        logger.error(f"Error generating embedding for query: {e}")
        return {"dense": [0.0] * 1024}

    return {"dense": [0.0] * 1024}
