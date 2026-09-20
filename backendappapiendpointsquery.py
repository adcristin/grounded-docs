
@router.get("/debug-retrieve")
async def debug_retrieve(query: str, rag_service: RAGService = Depends(get_rag_service)):
    from llama_index.core import QueryBundle
    retriever = rag_service.index.as_retriever(similarity_top_k=5)
    initial_nodes = retriever.retrieve(query)
    
    initial_results = []
    for node in initial_nodes[:3]:
        initial_results.append({"score": node.score, "text": node.get_content()})
        
    query_bundle = QueryBundle(query)
    reranked_nodes = rag_service.reranker.postprocess_nodes(initial_nodes, query_bundle=query_bundle)
    
    reranked_results = []
    for node in reranked_nodes[:3]:
        reranked_results.append({"score": node.score, "text": node.get_content()})
        
    return {
        "query": query,
        "initial": initial_results,
        "reranked": reranked_results
    }

@router.get("/debug-collection-count")
async def debug_collection_count(rag_service: RAGService = Depends(get_rag_service)):
    client = rag_service.vector_store.client
    collection_info = client.get_collection(collection_name=rag_service.vector_store.collection_name)
    return {"collection": rag_service.vector_store.collection_name, "points_count": collection_info.points_count}
