
import asyncio
import logging
from app.services.rag_service import RAGService
from app.core.config import settings
from llama_index.core import Settings, QueryBundle
from llama_index.core.vector_stores.types import VectorStoreQuery

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("debug_rag")

async def main():
    # Startup initialization (simulating main.py)
    from llama_index.embeddings.ollama import OllamaEmbedding
    Settings.embed_model = OllamaEmbedding(
        model_name=settings.EMBED_MODEL,
        base_url=settings.OLLAMA_BASE_URL
    )

    rag_service = RAGService()
    query_text = "What is the main purpose of this document?"

    print("\n--- RAG Debug Info ---")

    # 1. Model Instance Check
    print(f"Retriever embed_model type: {type(rag_service.embed_model)}")
    print(f"Is it the same instance as Settings.embed_model? {rag_service.embed_model is Settings.embed_model}")

    # 2. Query Embedding
    query_embedding = rag_service.embed_model.get_query_embedding(query_text)
    print(f"Raw query embedding (first 5): {query_embedding[:5]}")

    # 3. Pre-rerank scores
    # Use the real VectorStoreQuery type expected by the Qdrant vector store
    vs_query = VectorStoreQuery(
        query_embedding=query_embedding,
        similarity_top_k=settings.TOP_K_RETRIEVAL,
    )
    # The .query() method returns a VectorStoreQueryResult which has a .nodes property
    query_result = rag_service.vector_store.query(vs_query)
    initial_nodes = query_result.nodes
    pre_rerank_scores = [node.score for node in initial_nodes if hasattr(node, 'score')]
    print(f"Pre-rerank cosine similarity scores (top 5): {pre_rerank_scores[:5]}")

    # 4. Post-rerank scores
    # We use the production retrieval method to verify the fix
    retrieval_result = await rag_service.retrieve(query_text)
    candidates = retrieval_result.get("candidates", [])
    post_rerank_scores = [cand["score"] for cand in candidates]
    print(f"Post-rerank scores (top 5): {post_rerank_scores[:5]}")

    # 5. Groundedness Threshold
    print(f"Current groundedness threshold: {settings.RETRIEVAL_THRESHOLD}")
    print("----------------------\n")

if __name__ == "__main__":
    asyncio.run(main())
