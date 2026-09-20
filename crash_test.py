import asyncio
from app.services.rag_service import RAGService
from app.core.config import settings
from llama_index.core import QueryBundle

async def main():
    print("Initializing RAGService...")
    try:
        service = RAGService()
        print("RAGService initialized.")
        
        query = "Where is the headquarters?"
        print(f"Testing retrieval for: {query}")
        
        retriever = service.index.as_retriever(similarity_top_k=5)
        nodes = retriever.retrieve(query)
        print(f"Retrieved {len(nodes)} nodes.")
        
        print("Testing reranking...")
        query_bundle = QueryBundle(query)
        reranked = service.reranker.postprocess_nodes(nodes, query_bundle=query_bundle)
        print(f"Reranked to {len(reranked)} nodes.")
        
        for i, node in enumerate(reranked[:3]):
            print(f"Rank {i+1} | Score: {node.score:.4f} | Text: {node.get_content()[:50]}...")
            
    except Exception as e:
        print(f"Caught exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
