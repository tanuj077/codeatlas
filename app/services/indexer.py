import faiss
import numpy as np
import os
import pickle
import logging

logger = logging.getLogger(__name__)


class CodeIndexer:
    def __init__(self, dim: int, index_path="faiss.index", metadata_path="metadata.pkl"):
        """
        Args:
            dim (int): Dimension of your embeddings (e.g., 384 for MiniLM)
            index_path (str): Path to save/load FAISS index
            metadata_path (str): Path to store associated metadata
        """
        self.dim = dim
        self.index_path = index_path
        self.metadata_path = metadata_path

        self.index = faiss.IndexFlatL2(dim)
        self.metadata = []  # List of dicts (chunk info per vector)

        if os.path.exists(index_path) and os.path.exists(metadata_path):
            self.load()

    def add_embeddings(self, embeddings, metadata_list):
        """
        Add vectors and corresponding metadata.

        Args:
            embeddings (List[List[float]]): Vectors to index
            metadata_list (List[dict]): Metadata for each vector
        """
        if len(embeddings) != len(metadata_list):
            raise ValueError("Embeddings and metadata size mismatch")

        vectors = np.array(embeddings).astype('float32')
        self.index.add(vectors)
        self.metadata.extend(metadata_list)
        logger.info(f"Added {len(vectors)} vectors to index")

    def search(self, query_vector, top_k=5):
        """
        Search for nearest neighbors.

        Args:
            query_vector (List[float])
            top_k (int): Number of results

        Returns:
            List of (score, metadata) tuples
        """
        query = np.array([query_vector]).astype('float32')
        distances, indices = self.index.search(query, top_k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.metadata):
                results.append((dist, self.metadata[idx]))

        return results

    def save(self):
        try:
            faiss.write_index(self.index, self.index_path)
            with open(self.metadata_path, "wb") as f:
                pickle.dump(self.metadata, f)
            logger.info(f"Index and metadata saved to disk")
        except Exception as e:
            logger.error(f"Failed to save index or metadata: {e}")
            raise RuntimeError(f"Saving index failed: {e}") from e

    def load(self):
        try:
            self.index = faiss.read_index(self.index_path)
            with open(self.metadata_path, "rb") as f:
                self.metadata = pickle.load(f)
            logger.info(f"Loaded index with {len(self.metadata)} items")
            return True
        except Exception as e:
            logger.error(f"Failed to load index or metadata: {e}")
            self.index = faiss.IndexFlatL2(self.dim)
            self.metadata = []
            return False
