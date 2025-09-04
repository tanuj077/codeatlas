# app/services/searcher.py (fixed score interpretation)

import os
import numpy as np
from app.core.logger import logger
from app.services.indexer import CodeIndexer
from app.services.embedder import Embedder
from app.core.config import settings

class CodeSearcher:
    def __init__(self, embedder: Embedder, index_path="faiss.index", metadata_path="metadata.pkl"):
        self.embedder = embedder
        self.vector_store_dir = settings.VECTOR_STORE_DIR
        self.indexers = {}
        self.indexer = CodeIndexer(dim=self.embedder.dim, index_path=index_path, metadata_path=metadata_path)
        loaded = self.indexer.load()
        if loaded:
            repo_name = os.path.basename(os.path.dirname(index_path))
            self.indexers[repo_name] = self.indexer
            logger.info(f"Loaded index for repo '{repo_name}' with {len(self.indexer.metadata)} items")
        else:
            logger.warning("Started with an empty index. Run pipeline first.")

    def _get_indexer(self, repo_name: str) -> CodeIndexer:
        if repo_name in self.indexers:
            return self.indexers[repo_name]
        repo_path = os.path.join(self.vector_store_dir, repo_name)
        index_path = os.path.join(repo_path, "faiss.index")
        metadata_path = os.path.join(repo_path, "metadata.pkl")
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"Index file not found for repo '{repo_name}' at {index_path}")
        indexer = CodeIndexer(dim=self.embedder.dim, index_path=index_path, metadata_path=metadata_path)
        try:
            loaded = indexer.load()
            if not loaded:
                logger.warning(f"No index found for repo '{repo_name}'. Run pipeline first.")
        except Exception as e:
            logger.error(f"Failed to load index for repo '{repo_name}': {e}")
            raise RuntimeError(f"Index load failed for repo '{repo_name}'")
        self.indexers[repo_name] = indexer
        return indexer

    def semantic_search(self, repo_name: str, query: str, top_k=10):
        if not isinstance(query, str) or not query.strip():
            logger.warning("Query must be a non-empty string.")
            return []
        try:
            query_vec = self.embedder.embed([query])[0]
            indexer = self._get_indexer(repo_name)
            results = indexer.search(query_vec, top_k)
            
            # Log raw results for debugging
            logger.info(f"Raw search returned {len(results)} chunks with L2 distances: {[f'{r[0]:.2f}' for r in results]}")
            
            # For L2 distance, lower is better. Scores of 20-30 are reasonable for code search
            # Accept the best results without overly strict filtering
            filtered_results = results[:10]  # Take top 5 results
            
            logger.info(f"Using top {len(filtered_results)} chunks for query: {query}")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Search failed for repo '{repo_name}': {e}")
            return []
