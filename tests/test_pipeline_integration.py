import numpy as np
import pytest
from app.services import crawler, chunker, embedder, indexer

class DummyHFModel:
    def __init__(self, *args, **kwargs):
        pass
    def encode(self, texts, **kwargs):
        return np.array([[float(i)]*10 for i, _ in enumerate(texts)])
    def get_sentence_embedding_dimension(self):
        return 10

def test_pipeline_integration(tmp_path):
    # Create a dummy repo with Python file
    repo_dir = tmp_path/"repo"
    repo_dir.mkdir()
    file_path = repo_dir/"test.py"
    file_path.write_text("""def foo(): return 42
class Bar: pass""")
    
    files = crawler.collect_code_files(str(repo_dir))
    assert files, "Crawler should find files"
    
    try:
        print("File content:", file_path.read_text())
        chunks = chunker.extract_chunks(str(file_path), "python")
        print("Chunks are: ", chunks)
    except Exception as e:
        print("Chunker expection ", e)
    assert chunks, "Chunker should create chunks"
    
    emb = embedder.Embedder(backend="huggingface", hf_model="dummy")
    emb.model = DummyHFModel()
    texts = [c["code"] for c in chunks]
    vectors = emb.embed(texts)
    assert vectors, "Embedder should produce vectors"
    
    idx = indexer.CodeIndexer(dim=emb.dim, index_path=str(tmp_path/"faiss.index"),
                              metadata_path=tmp_path/"metadata.pkl")
    idx.add_embeddings(vectors, chunks)
    idx.save()
    assert (tmp_path/"faiss.index").exists(), "Index file should be saved"
    assert (tmp_path/"metadata.pkl").exists(), "Metadata file should be saved"