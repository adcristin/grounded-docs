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

@router.get("/debug-retrieve")
async def debug_retrieve(query: str, rag_service: RAGService = Depends(get_rag_service)):
    from llama_index.core import QueryBundle
    import qdrant_client
    
    # 1. Confirm collection name
    collection_name = rag_service.vector_store.collection_name
    print(f"[DEBUG] Collection name: {collection_name}")
    
    # 2. Confirm Qdrant client host/port
    qdrant_client_instance = rag_service.vector_store.client
    # Get the URL from the client's internal config
    qdrant_url = getattr(qdrant_client_instance, '_base_url', None) or getattr(qdrant_client_instance, 'url', None) or str(qdrant_client_instance)
    print(f"[DEBUG] Qdrant client URL: {qdrant_url}")
    
    # 3. Get query embedding and print first few values
    embed_model = rag_service.embed_model
    query_embedding = embed_model.get_query_embedding(query)
    print(f"[DEBUG] Query embedding (first 5 values): {query_embedding[:5] if query_embedding else 'None'}")
    print(f"[DEBUG] Query embedding length: {len(query_embedding) if query_embedding else 0}")
    
    # 4. Check retriever configuration for any filters
    retriever = rag_service.index.as_retriever(similarity_top_k=5)
    print(f"[DEBUG] Retriever similarity_top_k: {retriever.similarity_top_k}")
    print(f"[DEBUG] Retriever type: {type(retriever)}")
    print(f"[DEBUG] Retriever attributes: {[attr for attr in dir(retriever) if not attr.startswith('_')]}")
    
    # 5. Try with the real query
    initial_nodes = retriever.retrieve(query)
    print(f"[DEBUG] Initial nodes count for '{query}': {len(initial_nodes)}")
    
    # 6. Try with generic word "the" to rule out relevance filtering
    generic_query = "the"
    generic_nodes = retriever.retrieve(generic_query)
    print(f"[DEBUG] Initial nodes count for 'the': {len(generic_nodes)}")
    
    initial_results = []
    for node in initial_nodes[:3]:
        initial_results.append({"score": float(node.score), "text": node.get_content()})

    query_bundle = QueryBundle(query)
    reranked_nodes = rag_service.reranker.postprocess_nodes(initial_nodes, query_bundle=query_bundle)

    reranked_results = []
    for node in reranked_nodes[:3]:
        reranked_results.append({"score": float(node.score), "text": node.get_content()})

    # Also get generic query results for comparison
    generic_results = []
    for node in generic_nodes[:3]:
        generic_results.append({"score": float(node.score), "text": node.get_content()})

    return {
        "query": query,
        "debug": {
            "collection_name": collection_name,
            "qdrant_url": str(qdrant_url),
            "query_embedding_sample": [float(x) for x in query_embedding[:5]] if query_embedding else None,
            "query_embedding_dim": len(query_embedding) if query_embedding else 0,
            "retriever_similarity_top_k": retriever.similarity_top_k,
            "retriever_type": str(type(retriever)),
            "initial_nodes_count_real_query": len(initial_nodes),
            "initial_nodes_count_generic_query": len(generic_nodes),
        },
        "initial": initial_results,
        "generic_query_results": generic_results,
        "reranked": reranked_results
    }
