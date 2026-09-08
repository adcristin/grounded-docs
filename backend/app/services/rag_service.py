import logging
from typing import List, Dict, Any
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.postprocessor import SentenceTransformerRerank
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.qdrant import QdrantVectorStore
import qdrant_client

from app.core.config import settings
from app.core.storage import get_vector_store

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        # 1. Setup LLM and Embedding models via Ollama
        self.llm = Ollama(
            model=settings.LLM_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            request_timeout=120.0
        )
        self.embed_model = OllamaEmbedding(
            model_name=settings.EMBED_MODEL,
            base_url=settings.OLLAMA_BASE_URL
        )

        # 2. Setup Qdrant Vector Store
        # We use the storage interface but for LlamaIndex we need the actual VectorStore object
        self.vector_store = QdrantVectorStore(
            client=qdrant_client.QdrantClient(url=settings.QDRANT_URL),
            collection_name=settings.QDRANT_COLLECTION
        )

        # 3. Initialize Index
        self.index = VectorStoreIndex.from_vector_store(
            vector_store=self.vector_store,
            embed_model=self.embed_model
        )

        # 4. Setup Reranker (The "Noise Filter")
        self.reranker = SentenceTransformerRerank(
            model=settings.RERANK_MODEL,
            top_n=settings.TOP_K_RERANK
        )

    def _build_grounded_prompt(self, query: str, context_str: str) -> str:
        """
        Constructs a strict grounding prompt.
        """
        return (
            f"You are a strict Q&A assistant. Answer the question using ONLY the provided context.\n\n"
            f"CONTEXT:\n{context_str}\n\n"
            f"QUESTION: {query}\n\n"
            f"INSTRUCTIONS:\n"
            f"1. Use only the provided context. Do not use external knowledge.\n"
            f"2. Every claim must include a citation in the format [Source: filename, page X].\n"
            f"3. If the context does not contain the answer, strictly respond with: 'Insufficient context to answer the question.'\n"
            f"4. Do not apologize or explain your constraints.\n\n"
            f"ANSWER:"
        )

    async def query(self, user_query: str):
        # Step 1: Initial Retrieval (Wide net)
        retriever = self.index.as_retriever(similarity_top_k=settings.TOP_K_RETRIEVAL)
        initial_nodes = retriever.retrieve(user_query)

        if not initial_nodes:
            return {"answer": "Insufficient context: No relevant documents found.", "sources": []}

        # Step 2: Reranking (Precision filter)
        # The reranker takes the query and the nodes, and returns only the top-N most relevant ones
        reranked_nodes = self.reranker.postprocess_nodes(initial_nodes, query_bundle=user_query)

        # Step 3: Confidence Thresholding
        # We check the score of the top reranked node.
        # Note: Reranker scores are different from vector distance.
        # BGE-Reranker typically produces a logit score.
        top_score = reranked_nodes[0].score if reranked_nodes else 0

        # Since reranker scores vary by model, we might need to calibrate this.
        # For now, we implement the check.
        if top_score < settings.RETRIEVAL_THRESHOLD:
             return {
                 "answer": "Insufficient context: The retrieved information is not confident enough to provide a grounded answer.",
                 "sources": []
             }

        # Step 4: Context Synthesis
        context_parts = []
        for node in reranked_nodes:
            meta = node.metadata
            ctx = f"[Source: {meta.get('source_filename', 'unknown')}, page {meta.get('page_number', 'unknown')}] {node.get_content()}"
            context_parts.append(ctx)

        context_str = "\n\n".join(context_parts)

        # Step 5: Grounded Generation
        prompt = self._build_grounded_prompt(user_query, context_str)
        response = self.llm.complete(prompt)

        return {
            "answer": response.text,
            "sources": [node.metadata for node in reranked_nodes]
        }
