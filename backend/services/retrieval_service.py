from functools import lru_cache
from backend.core.config import settings
from rag.retrieval.retriever import Retriever

@lru_cache
def get_retriever():
    return Retriever(settings.index_dir)

def retrieve(query):
    return get_retriever().search(query, settings.top_k)
