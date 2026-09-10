import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)

router = APIRouter()

# We'll use a simple global instance for the RAGService to avoid reloading models on every request
# In a larger app, we'd use a proper dependency injection container or a singleton.
rag_service = RAGService()

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
async def retrieve_context(request: QueryRequest):
    try:
        result = await rag_service.retrieve(request.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")

@router.post("/query", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    try:
        result = await rag_service.query(request.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@router.post("/chat", response_model=ChatResponse)
async def chat_with_docs(request: ChatRequest):
    try:
        result = await rag_service.chat(request.query, model=request.model)
        return result
    except Exception as e:
        logger.error(f"Chat failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")
