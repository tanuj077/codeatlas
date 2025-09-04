import argparse
import os
import logging
from app.services.crawler import collect_code_files
from app.services.chunker import extract_chunks
from app.services.embedder import Embedder
from app.services.indexer import CodeIndexer
from app.utils.repo_utils import compute_repo_hash, get_repo_hash_path, load_repo_hash, save_repo_hash
from app.core.config import settings

logger = logging.getLogger(__name__)

def run_pipeline(repo_path: str, backend: str = settings.EMBEDDER_BACKEND):
    if not os.path.isdir(repo_path):
        raise ValueError(f"Invalid repo path: {repo_path}")

    repo_name = os.path.basename(os.path.abspath(repo_path))
    try:
        repo_hash_path = get_repo_hash_path(repo_name)
        current_hash = compute_repo_hash(repo_path)
        previous_hash = load_repo_hash(repo_name)

        if previous_hash == current_hash:
            logger.info(f"Skipping indexing for '{repo_name}' — no changes detected.")
            return

        save_repo_hash(repo_name, current_hash)

        index_dir = os.path.join(settings.VECTOR_STORE_DIR, repo_name)
        os.makedirs(index_dir, exist_ok=True)

        index_path = os.path.join(index_dir, "faiss.index")
        metadata_path = os.path.join(index_dir, "metadata.pkl")

        code_files = collect_code_files(repo_path)
        logger.info(f"Found {len(code_files)} code files in {repo_path}")

        # Pass hf_model from settings if using HuggingFace backend
        embedder_kwargs = {}
        if backend == "huggingface":
            embedder_kwargs["hf_model"] = settings.EMBEDDING_MODEL_NAME

        embedder = Embedder(backend=backend, **embedder_kwargs)
        indexer = CodeIndexer(dim=embedder.dim, index_path=index_path, metadata_path=metadata_path)

        for file_path, language in code_files:
            chunks = extract_chunks(file_path, language)
            if not chunks:
                continue

            texts = [chunk["code"] for chunk in chunks]

            try:
                vectors = embedder.embed(texts)
            except Exception as e:
                logger.warning(f"Skipping {file_path} due to embedding error: {e}")
                continue

            metadata_list = [
                {
                    "path": file_path,
                    "name": chunk["name"],
                    "type": chunk["type"],
                    "start_line": chunk["start_line"],
                    "end_line": chunk["end_line"],
                }
                for chunk in chunks
            ]

            indexer.add_embeddings(vectors, metadata_list)

        indexer.save()
        logger.info(f"Indexed {len(indexer.metadata)} code chunks for repo '{repo_name}'.")

    except Exception as e:
        logger.exception(f"Pipeline failed for repo '{repo_name}': {e}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CodeAtlas Repository Indexing Pipeline")
    parser.add_argument("repo_path", help="Path to the code repository to index")
    parser.add_argument("--backend", default=settings.EMBEDDER_BACKEND, help="Embedding backend to use")

    args = parser.parse_args()

    run_pipeline(repo_path=args.repo_path, backend=args.backend)
