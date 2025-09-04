import pytest
from app.services.embedder import Embedder
import app.services.embedder as embedder_mod
import numpy as np

class DummyOpenAI:
    class Embedding:
        @staticmethod
        def create(model, input):
            raise Exception("API Failure")

class DummySentenceTransformer:
    def __init__(self, *args, **kwargs):
        pass
    def encode(self, texts, **kwargs):
        return np.array([[float(i)]*10 for i, _ in enumerate(texts)])
    def get_sentence_embedding_dimension(self):
        return 10

def test_huggingface_init_requires_model():
    try:
        Embedder(backend="huggingface")
        assert False, "Should raise ValueError if hf_model not provided"
    except ValueError as e:
        assert "hf_model must be provided" in str(e)

def test_huggingface_embedding_output():
    embedder_mod.SentenceTransformer = DummySentenceTransformer
    embedder = Embedder(backend="huggingface", hf_model="dummy")
    texts = ["Hello World", "CodeAtlas"]
    vectors = embedder.embed(texts)
    assert len(vectors) == len(texts)
    assert all(len(vec) == embedder.dim for vec in vectors)
    
def test_openai_embedder_runtime_error(monkeypatch):
    monkeypatch.setattr("app.services.embedder.openai", DummyOpenAI)
    embedder = Embedder(backend="openai", openai_model="text-embedding-3-small", openai_api_key="dummy")
    try:
        embedder.embed(["test"])
        assert False, "Should raise RuntimeError or OpenAI API failure"
    except RuntimeError as e:
        assert "Failed to generate embeddings via OpenAI" in str(e)
                
def test_openai_embedder_dimension(monkeypatch):
    monkeypatch.setattr("app.services.embedder.openai", DummyOpenAI)
    embedder = Embedder(backend="openai", openai_model="text-embedding-3-small", openai_api_key="dummy")
    assert embedder.dim == 1536

