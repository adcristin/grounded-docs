import asyncio
from app.services.rag_service import RAGService
from app.core.config import settings

async def main():
    service = RAGService()
    query = "Where is the headquarters?"
    
    # We manually trigger the retrieval steps to see the gap
    from llama_index.core import QueryBundle
    
    # Step 1: Initial Retrieval
    # Use the index's retriever directly as in the current code
    retriever = service.index.as_retriever(similarity_top_k=settings.TOP_K_RETRIEVAL)
    initial_nodes = retriever.retrieve(query)
    
    print("\n--- INITIAL RETRIEVAL TOP 3 ---")
    for i, node in enumerate(initial_nodes[:3]):
        print(f"Rank {i+1} | Score: {node.score:.4f} | Text: {node.get_content()[:100]}...")

    # Step 2: Reranking
    query_bundle = QueryBundle(query)
    reranked_nodes = service.reranker.postprocess_nodes(initial_nodes, query_bundle=query_bundle)
    
    print("\n--- RERANKED TOP 3 ---")
    for i, node in enumerate(reranked_nodes[:3]):
        print(f"Rank {i+1} | Score: {node.score:.4f} | Text: {node.get_content()[:100]}...")

if __name__ == "__main__":
    asyncio.run(main())
