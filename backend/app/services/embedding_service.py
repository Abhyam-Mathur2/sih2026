from __future__ import annotations

import logging
from sentence_transformers import SentenceTransformer
from app.core.config import settings

logger = logging.getLogger("embedding_service")
_model = None


def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info(f"Loading SentenceTransformer model: {settings.embedding_model}")
        _model = SentenceTransformer(settings.embedding_model, cache_folder=settings.model_cache_dir)
    return _model


def generate_embedding(text: str) -> list[float]:
    """Generate a vector embedding for the given text."""
    model = get_embedding_model()
    emb = model.encode(text, convert_to_numpy=True)
    return [float(x) for x in emb]
