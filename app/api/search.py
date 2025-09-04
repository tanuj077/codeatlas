from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_code_searcher
from app.services.searcher import CodeSearcher
from app.core.logger import logger

router = APIRouter()

@router.get("")
def search_endpoint(
    repo_name: str,
    query: str,
    top_k: int = 5,
    searcher: CodeSearcher = Depends(get_code_searcher)
):
    """
    Perform semantic search over indexed code.
    """
    if not query.strip():
        logger.warning("Received empty search query")
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        logger.info(f"Search request - repo: {repo_name}, query: '{query}', top_k: {top_k}")

        results = searcher.semantic_search(repo_name, query, top_k)

        formatted = [
            {
                "score": float(score),
                "path": meta["path"],
                "name": meta["name"],
                "type": meta["type"],
                "start_line": meta["start_line"],
                "end_line": meta["end_line"]
            }
            for score, meta in results
        ]

        logger.info(f"Search results - repo: {repo_name}, matches found: {len(formatted)}")
        return {"results": formatted}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during search in repo: {repo_name}")
        raise HTTPException(status_code=500, detail="Internal server error")
