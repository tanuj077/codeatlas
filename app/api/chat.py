from fastapi import APIRouter, Depends, Query, Body, HTTPException
from pydantic import BaseModel
from app.services.chat_service import ChatService
from app.dependencies import get_chat_service
from app.core.logger import logger

router = APIRouter()

class ChatQuery(BaseModel):
    query: str

@router.post("")
def chat_endpoint(
    repo_name: str = Query(..., description="Repository name to query"),
    payload: ChatQuery = Body(..., description="User query payload"),
    chat_service: ChatService = Depends(get_chat_service),
):
    try:
        logger.info(f"Received chat request | repo={repo_name} | query='{payload.query}'")

        response = chat_service.answer_question(repo_name, payload.query)

        logger.info(f"Response generated successfully | repo={repo_name}")
        return {"answer": response}

    except ValueError as ve:
        logger.warning(f"Validation error | repo={repo_name} | error={str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        logger.exception(f"Unexpected error in chat_endpoint | repo={repo_name}")
        raise HTTPException(status_code=500, detail="Internal server error")
