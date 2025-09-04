import os
import hashlib
import pickle
from typing import Optional
from app.core.config import settings
from app.core.logger import logger


def compute_repo_hash(repo_path: str) -> str:
    """Recursively walk the repo and hash file contents + names."""
    sha = hashlib.sha256()

    for root, _, files in os.walk(repo_path):
        for file in sorted(files):
            file_path = os.path.join(root, file)
            try:
                with open(file_path, "rb") as f:
                    while chunk := f.read(8192):
                        sha.update(chunk)
                sha.update(file.encode())  
            except Exception as e:
                logger.warning(f"Skipping unreadable file: {file_path} ({e})")

    return sha.hexdigest()


def get_repo_hash_path(repo_name: str) -> str:
    """Returns path to the hash cache file for a given repo."""
    try:
        os.makedirs(settings.VECTOR_STORE_DIR, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create vector store directory: {settings.VECTOR_STORE_DIR} ({e})")
        raise
    return os.path.join(settings.VECTOR_STORE_DIR, f"{repo_name}.hash")


def load_repo_hash(repo_name: str) -> Optional[str]:
    """Loads the stored repo hash if available."""
    path = get_repo_hash_path(repo_name)
    if not os.path.exists(path):
        logger.info(f"No stored hash found for repo '{repo_name}'.")
        return None
    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        logger.error(f"Failed to load repo hash for '{repo_name}': {e}", exc_info=True)
        return None


def save_repo_hash(repo_name: str, repo_hash: str):
    """Saves the computed repo hash to disk."""
    path = get_repo_hash_path(repo_name)
    try:
        with open(path, "wb") as f:
            pickle.dump(repo_hash, f)
        logger.debug(f"Saved repo hash for '{repo_name}' at {path}")
    except Exception as e:
        logger.error(f"Failed to save repo hash for '{repo_name}': {e}", exc_info=True)
