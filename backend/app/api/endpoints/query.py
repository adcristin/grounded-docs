import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from functools import lru_cache
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)

router = APIRouter()

@lru_cache
def get_rag_service():
    """
    Provides a singleton instance of RAGService.
    Using lru_cache ensures the service (and its models) are only loaded once.
    """
    return RAGService()

class QueryRequest(BaseModel):
    query: str

class RetrieveResponse(BaseModel):
    grounded: bool
    candidates: list
    logs: dict

class QueryResponse(BaseModel):
    answer: str
    sources: list

class ChatRequest(BaseModel):
    query: str
    model: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    citations: List[Dict[str, Any]]
    debug: Dict[str, Any]

@router.post("/retrieve", response_model=RetrieveResponse)
async def retrieve_context(request: QueryRequest, rag_service: RAGService = Depends(get_rag_service)):
    try:
        result = await rag_service.retrieve(request.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")

@router.post("/query", response_model=QueryResponse)
async def ask_question(request: QueryRequest, rag_service: RAGService = Depends(get_rag_service)):
    try:
        result = await rag_service.query(request.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@router.post("/chat", response_model=ChatResponse)
async def chat_with_docs(request: ChatRequest, rag_service: RAGService = Depends(get_rag_service)):
    try:
        result = await rag_service.chat(request.query, model=request.model)
        return result
    except Exception as e:
        logger.error(f"Chat failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")
