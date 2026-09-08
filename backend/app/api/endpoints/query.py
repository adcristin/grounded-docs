from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.services.rag_service import RAGService

router = APIRouter()

# We'll use a simple global instance for the RAGService to avoid reloading models on every request
# In a larger app, we'd use a proper dependency injection container or a singleton.
rag_service = RAGService()

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str
    sources: list

@router.post("/query", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    try:
        result = await rag_service.query(request.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")
