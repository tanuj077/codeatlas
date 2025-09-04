import os
from functools import lru_cache
from fastapi import Query
from app.services.chat_service import ChatService
from app.services.llm_huggingface import HuggingFaceChat
from app.services.llm_openai import OpenAIChat
from app.services.embedder import Embedder
from app.services.searcher import CodeSearcher
from app.services.chunker import extract_chunks
from app.core.config import settings

# ---- Shared Embedder (cached) ----
@lru_cache()
def get_embedder() -> Embedder:
    return Embedder(
        backend=settings.EMBEDDER_BACKEND,
        hf_model=settings.EMBEDDING_MODEL_NAME,
        openai_model=settings.LLM_MODEL_NAME,
        openai_api_key=settings.OPENAI_API_KEY,
    )

# ---- Cached Chat Backends ----
@lru_cache(maxsize=1)  # Singleton-like caching for heavy LLM
def get_hf_chat() -> HuggingFaceChat:
    return HuggingFaceChat()

@lru_cache(maxsize=1)
def get_openai_chat() -> OpenAIChat:
    return OpenAIChat()

# ChatService Dependency (Dynamic per-repo)
def get_chat_service(repo_name: str = Query(...)) -> ChatService:
    embedder = get_embedder()
    vector_store_path = os.path.join(settings.VECTOR_STORE_DIR, repo_name)
    index_path = os.path.join(vector_store_path, "faiss.index")
    metadata_path = os.path.join(vector_store_path, "metadata.pkl")
    if not os.path.exists(index_path) or not os.path.exists(metadata_path):
        raise FileNotFoundError(
            f"[CodeAtlas] Vector index for repo '{repo_name}' not found.\n"
            f"Expected: {index_path} and {metadata_path}.\n"
            f"Run the indexing pipeline for this repo first."
        )
    searcher = CodeSearcher(
        index_path=index_path,
        metadata_path=metadata_path,
        embedder=embedder
    )
    chunker = extract_chunks
    hf_chat = get_hf_chat() if not settings.USE_OPENAI else None
    openai_chat = get_openai_chat() if settings.USE_OPENAI else None
    return ChatService(searcher, chunker, hf_chat, openai_chat)

# CodeSearcher Dependency (Dynamic per-repo)
def get_code_searcher(repo_name: str = Query(...)) -> CodeSearcher:
    embedder = get_embedder()
    vector_store_path = os.path.join(settings.VECTOR_STORE_DIR, repo_name)
    index_path = os.path.join(vector_store_path, "faiss.index")
    metadata_path = os.path.join(vector_store_path, "metadata.pkl")
    if not os.path.exists(index_path) or not os.path.exists(metadata_path):
        raise FileNotFoundError(
            f"[CodeAtlas] Vector index for repo '{repo_name}' not found.\n"
            f"Expected: {index_path} and {metadata_path}.\n"
            f"Run the indexing pipeline for this repo first."
        )
    return CodeSearcher(
        index_path=index_path,
        metadata_path=metadata_path,
        embedder=embedder
    )
