from __future__ import annotations

import logging
from app.core.config import settings

logger = logging.getLogger("embedding_service")
_model = None


def get_embedding_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading SentenceTransformer model: {settings.embedding_model}")
            _model = SentenceTransformer(settings.embedding_model, cache_folder=settings.model_cache_dir)
        except Exception as e:
            logger.warning(f"Could not load SentenceTransformer: {e}")
            return None
    return _model


def generate_embedding(text: str) -> list[float]:
    """Generate a vector embedding for the given text."""
    try:
        model = get_embedding_model()
        if model is None:
            return []
        emb = model.encode(text, convert_to_numpy=True)
        return [float(x) for x in emb]
    except Exception as e:
        logger.warning(f"Error encoding text: {e}")
        return []
