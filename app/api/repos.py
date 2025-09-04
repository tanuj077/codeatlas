from fastapi import APIRouter, HTTPException
from pathlib import Path
from app.core.config import settings
from app.core.logger import logger

router = APIRouter()

@router.get("/")
def list_indexed_repos():
    try:
        root = Path(settings.VECTOR_STORE_DIR)

        if not root.exists() or not root.is_dir():
            logger.warning(f"Vector store directory not found: {root}")
            raise HTTPException(status_code=404, detail="Vector store directory not found")

        repos = [p.name for p in root.iterdir() if p.is_dir()]

        logger.info(f"Indexed repositories found: {repos}")
        return {"repos": repos}

    except HTTPException:
        # re-raise so FastAPI handles it properly
        raise

    except Exception as e:
        logger.exception("Unexpected error while listing indexed repositories")
        raise HTTPException(status_code=500, detail="Internal server error")
