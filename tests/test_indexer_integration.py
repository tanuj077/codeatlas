from app.services.embedder import Embedder
from app.services.indexer import CodeIndexer
import numpy as np

class DummyHFModel:
    def encode(self, texts, **kwargs):
        return np.array([[float(i)]*10 for i, _ in enumerate(texts)])
    def get_sentence_embedding_dimension(self):
        return 10
    
def test_indexer_matches_embedder_dim(tmp_path):
    embedder = Embedder(backend="huggingface", hf_model="dummy")
    embedder.model = DummyHFModel()
    index_path = tmp_path/"test.index"
    metadata_path = tmp_path/"test.pkl"

    indexer = CodeIndexer(dim=embedder.dim, index_path=str(index_path), metadata_path=str(metadata_path))
    vectors = [ [0.1] * embedder.dim, [0.2] * embedder.dim ]
    metadata = [ {"path": "dummy1"}, {"path": "dummy2"} ]

    indexer.add_embeddings(vectors, metadata)
    indexer.save()

    assert index_path.exists(), "Index file should be saved"
    assert metadata_path.exists(), "Metadata file should be saved"
