import pytest
from app.services.chat_service import ChatService
from app.services.llm_huggingface import HuggingFaceChat
from app.services.llm_openai import OpenAIChat
from app.services.searcher import CodeSearcher
from app.services.chunker import extract_chunks
from app.core import config

class DummyChunker:
    def extract_chunks(self, file_path, language):
        return [
            {"code": "def dummy_func(): pass", "type": "function", "name": "dummy_func", 
             "start_line": 1, "end_line": 1}
        ]

class DummySearcher:
    def semantic_search(self, repo_name, query, top_k=5):
        return [(0.9, {"path": "dummy.py", "name": "dummy_func", "type": "function",
                       "start_line": 1, "end_line": 2})]
        
class DummyHFChat:
    def chat(self, question, context):
        return {"answer": "Dummy HuggingFace answer"}
    
class DummyOpenAIChat:
    def chat(self, question, context):
        return {"answer": "Dummy OpenAI answer"}
    
def test_chat_service_hf_backend(monkeypatch):
    monkeypatch.setattr(config.settings, "CODEATLAS_CHAT_BACKEND", "huggingface")
    chat_service = ChatService(DummySearcher(), DummyChunker(), DummyHFChat(), DummyOpenAIChat())
    backend = chat_service.get_chat_backend()
    assert isinstance(backend, DummyHFChat)

def test_chat_service_openai_backend(monkeypatch):
    monkeypatch.setattr(config.settings, "CODEATLAS_CHAT_BACKEND", "openai")
    chat_service = ChatService(DummySearcher(), DummyChunker(), DummyHFChat(), DummyOpenAIChat())
    backend = chat_service.get_chat_backend()
    assert isinstance(backend, DummyOpenAIChat)