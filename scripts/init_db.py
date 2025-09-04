import os
from pathlib import Path
from app.core.config import settings
from app.core.logger import logger
from scripts.run_pipeline import run_pipeline
from app.utils.repo_utils import compute_repo_hash, load_repo_hash, save_repo_hash

def init_repos():
    repo_root = Path(settings.REPO_ROOT)

    if not repo_root.exists():
        logger.error(f"Repo root path '{repo_root}' does not exist.")
        return

    for repo_path in repo_root.iterdir():
        if not repo_path.is_dir():
            continue

        repo_name = repo_path.name
        try:
            current_hash = compute_repo_hash(str(repo_path))
            saved_hash = load_repo_hash(repo_name)

            if saved_hash == current_hash:
                logger.info(f"[{repo_name}] No changes detected. Skipping indexing.")
                continue

            logger.info(f"[{repo_name}] Indexing started...")
            run_pipeline(str(repo_path))
            save_repo_hash(repo_name, current_hash)
            logger.info(f"[{repo_name}] Indexing complete ✅")

        except Exception as e:
            logger.error(f"[{repo_name}] Failed to index repository: {e}", exc_info=True)

if __name__ == "__main__":
    # Index all repos at startup
    init_repos()
