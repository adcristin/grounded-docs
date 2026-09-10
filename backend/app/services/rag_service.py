import logging
import re
from typing import List, Dict, Any
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.postprocessor import SentenceTransformerRerank
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.core.llms import ChatMessage
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

    async def retrieve(self, user_query: str):
        """
        Performs the retrieval and reranking pipeline.
        Returns the top candidates and whether they passed the groundedness gate.
        """
        # Step 1: Initial Retrieval (Wide net)
        retriever = self.index.as_retriever(similarity_top_k=settings.TOP_K_RETRIEVAL)
        initial_nodes = retriever.retrieve(user_query)

        if not initial_nodes:
            logger.info(f"Query: {user_query} | Initial retrieval: 0 nodes")
            return {"grounded": False, "candidates": [], "logs": {"initial_count": 0}}

        # Log initial cosine similarity scores (approximate)
        initial_scores = [node.score for node in initial_nodes if hasattr(node, 'score')]
        logger.info(f"Query: {user_query} | Initial scores (top 5): {initial_scores[:5]}")

        # Step 2: Reranking (Precision filter)
        reranked_nodes = self.reranker.postprocess_nodes(initial_nodes, query_bundle=user_query)

        # Step 3: Confidence Thresholding
        top_score = reranked_nodes[0].score if reranked_nodes else 0
        logger.info(f"Query: {user_query} | Top reranker score: {top_score}")

        if top_score < settings.RETRIEVAL_THRESHOLD:
            return {
                "grounded": False,
                "candidates": [],
                "logs": {
                    "initial_top_score": initial_scores[0] if initial_scores else 0,
                    "rerank_top_score": top_score
                }
            }

        # Step 4: Prepare Candidates
        candidates = []
        for node in reranked_nodes:
            meta = node.metadata
            candidates.append({
                "text": node.get_content(),
                "score": node.score,
                "metadata": {
                    "source_filename": meta.get('source_filename', 'unknown'),
                    "page_number": meta.get('page_number', 'unknown')
                }
            })

        return {
            "grounded": True,
            "candidates": candidates,
            "logs": {
                "initial_top_score": initial_scores[0] if initial_scores else 0,
                "rerank_top_score": top_score
            }
        }

    async def query(self, user_query: str):
        """
        Backward compatibility wrapper for the /query endpoint.
        """
        result = await self.chat(user_query)
        return {
            "answer": result["answer"],
            "sources": [c for c in result["citations"]]
        }

    async def chat(self, user_query: str, model: str = None):

        """
        Orchestrates the full RAG pipeline: retrieve -> groundedness gate -> generate -> parse citations.
        """
        # 1. Retrieval and Groundedness Gate
        retrieval_result = await self.retrieve(user_query)

        if not retrieval_result["grounded"]:
            logger.info(f"[CHAT_QUERY] Query: {user_query} | Model: {model or settings.LLM_MODEL} | Grounded: False")
            return {
                "answer": "Insufficient context to answer the question.",
                "citations": [],
                "debug": {
                    "grounded": False,
                    "initial_top_score": retrieval_result["logs"].get("initial_top_score", 0),
                    "rerank_top_score": retrieval_result["logs"].get("rerank_top_score", 0),
                    "chunk_count": 0
                }
            }

        candidates = retrieval_result["candidates"]
        top_score = retrieval_result["logs"].get("rerank_top_score", 0)
        selected_model = model or settings.LLM_MODEL

        # 2. Context Assembly
        context_parts = []
        for i, cand in enumerate(candidates, 1):
            ctx = f"[{i}] {cand['text']}"
            context_parts.append(ctx)
        context_str = "\n\n".join(context_parts)

        # 3. Grounded Generation
        # Use the specific model for this request
        llm = Ollama(
            model=selected_model,
            base_url=settings.OLLAMA_BASE_URL,
            request_timeout=120.0
        )

        prompt_data = self._build_chat_prompt(user_query, context_str)
        messages = [
            ChatMessage(role="system", content=prompt_data["system"]),
            ChatMessage(role="user", content=prompt_data["user"]),
        ]
        response = llm.chat(messages)
        answer = response.message.content

        # 4. Citation Parsing and Validation
        citations = self._parse_citations(answer, candidates, user_query)

        # 5. Structured Logging
        cited_indices = [c["chunk_index"] for c in citations]
        logger.info(
            f"[CHAT_QUERY] Query: {user_query} | Model: {selected_model} | "
            f"Grounded: True | Top Score: {top_score:.4f} | Validated Citations: {cited_indices}"
        )

        return {
            "answer": answer,
            "citations": citations,
            "debug": {
                "grounded": True,
                "initial_top_score": retrieval_result["logs"].get("initial_top_score", 0),
                "rerank_top_score": retrieval_result["logs"].get("rerank_top_score", 0),
                "chunk_count": len(candidates)
            }
        }

    def _build_chat_prompt(self, query: str, context_str: str) -> Dict[str, str]:
        """
        Returns the strict grounded prompt template.
        """
        return {
            "system": (
                "You are a strict Q&A assistant. Answer the question using ONLY the provided context. "
                "Every claim must be cited using numeric markers like [1], [2], etc., referring to the provided context chunks. "
                "If the context does not contain the answer, strictly respond with: 'Insufficient context to answer the question.' "
                "Do not use external knowledge. Do not apologize or explain constraints."
            ),
            "user": f"CONTEXT:\n{context_str}\n\nQUESTION: {query}"
        }

    def _parse_citations(self, answer: str, candidates: List[Dict], query: str) -> List[Dict]:
        """
        Extracts [n] markers and maps them to source chunks with range validation.
        """
        # Find all numeric markers [1], [2], etc.
        markers = re.findall(r"\[(\d+)\]", answer)
        valid_citations = []
        seen_indices = set()

        for marker in markers:
            try:
                idx = int(marker)
                # Range Validation: 1-based index must be within [1, len(candidates)]
                if 1 <= idx <= len(candidates):
                    if idx not in seen_indices:
                        cand = candidates[idx - 1]
                        valid_citations.append({
                            "chunk_index": idx,
                            "source_filename": cand["metadata"]["source_filename"],
                            "page_number": cand["metadata"]["page_number"],
                            "text": cand["text"]
                        })
                        seen_indices.add(idx)
                else:
                    logger.info(f"[CHAT_ANOMALY] Hallucinated index {idx} for query {query}")
            except ValueError:
                continue

        return valid_citations
