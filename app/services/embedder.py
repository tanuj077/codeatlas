# app/services/embedder.py (reverted to previous approach: hf_model=None with enforcement, openai_model with default)

import os
import logging
from typing import List
from sentence_transformers import SentenceTransformer
try:
    import openai
except ImportError:
    openai = None  # Safe fallback if OpenAI package not installed

logger = logging.getLogger(__name__)

class Embedder:
    def __init__(self, backend="huggingface", hf_model=None, openai_model="text-embedding-3-small", openai_api_key=None):
        self.backend = backend.lower()

        if self.backend == "huggingface":
            if not hf_model:
                raise ValueError("hf_model must be provided for HuggingFace backend (set EMBEDDING_MODEL_NAME in .env)")
            self.model = SentenceTransformer(hf_model)
            self.dim = self.model.get_sentence_embedding_dimension()
            logger.info(f"Loaded HuggingFace model: {hf_model} with dimension {self.dim}")

        elif self.backend == "openai":
            if openai is None:
                raise ImportError("OpenAI package not installed. Run: pip install openai")
            self.openai_model = openai_model
            openai.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
            if not openai.api_key:
                raise ValueError("OpenAI API key required for OpenAI backend.")

            # Adjusted dimension handling for OpenAI models
            if "text-embedding-3" in openai_model:
                self.dim = 1536
            else:
                self.dim = 768

            logger.info(f"Using OpenAI model: {openai_model} with dimension {self.dim}")

        else:
            raise ValueError("Unsupported backend. Use 'huggingface' or 'openai'.")

    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts (List[str]): Input texts/snippets

        Returns:
            List of embedding vectors

        Raises:
            RuntimeError on failure to generate embeddings
        """
        if self.backend == "huggingface":
            return self.model.encode(texts, show_progress_bar=False, convert_to_numpy=True).tolist()

        elif self.backend == "openai":
            try:
                response = openai.Embedding.create(
                    model=self.openai_model,
                    input=texts
                )
                return [e["embedding"] for e in response["data"]]

            except Exception as e:
                logger.error(f"OpenAI embedding error: {e}")
                raise RuntimeError(f"Failed to generate embeddings via OpenAI: {e}") from e
