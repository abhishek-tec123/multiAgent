from functools import lru_cache

from app.core.dependencies import get_embeddings
from app.services.reterever import RetrieverService


@lru_cache(maxsize=1)
def get_retriever_service() -> RetrieverService:
    embeddings = get_embeddings()
    return RetrieverService(embeddings=embeddings)

# Backwards-compatible alias for existing imports
retriever_service = get_retriever_service()
