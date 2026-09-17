from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.ollama import OllamaEmbedding
import qdrant_client
from app.core.config import settings

class VectorStoreInterface(ABC):
    @abstractmethod
    def add_chunks(self, chunks: List[Dict[str, Any]]):
        """Add a list of text chunks with metadata to the store."""
        pass

    @abstractmethod
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve the most similar chunks for a given query."""
        pass

    @abstractmethod
    def clear(self):
        """Clear the storage."""
        pass

class QdrantStorage(VectorStoreInterface):
    def __init__(self):
        self.client = qdrant_client.QdrantClient(url=settings.QDRANT_URL)
        self.vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=settings.QDRANT_COLLECTION
        )
        self._ensure_collection()

    def _ensure_collection(self):
        """Creates the collection if it doesn't already exist."""
        try:
            self.client.get_collection(collection_name=settings.QDRANT_COLLECTION)
        except qdrant_client.http.exceptions.UnexpectedResponse as e:
            if "Not found" in str(e):
                self.client.create_collection(
                    collection_name=settings.QDRANT_COLLECTION,
                    vectors_config=qdrant_client.models.VectorParams(
                        size=768,
                        distance=qdrant_client.models.Distance.COSINE
                    )
                )
            else:
                raise e

    def add_chunks(self, chunks: List[Dict[str, Any]]):
        from llama_index.core.schema import TextNode
        from llama_index.embeddings.ollama import OllamaEmbedding
        import logging
        logger = logging.getLogger(__name__)

        embed_model = OllamaEmbedding(
            model_name=settings.EMBED_MODEL,
            base_url=settings.OLLAMA_BASE_URL
        )

        nodes = [
            TextNode(
                text=chunk["text"],
                id_=chunk.get("id"),
                metadata=chunk["metadata"]
            )
            for chunk in chunks
        ]

        try:
            # Manually embed the nodes
            embeddings = embed_model.get_text_embedding_batch([node.get_content() for node in nodes])
            for node, emb in zip(nodes, embeddings):
                node.embedding = emb

            # Now add them to the vector store
            self.vector_store.add(nodes)
        except Exception as e:
            logger.exception(f"Error adding chunks to vector store: {str(e)}")
            raise e

    def retrieve(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve the most similar chunks using a pre-computed query embedding."""
        from llama_index.core.schema import NodeWithScore

        # Use Qdrant's search method to find vectors closest to the query_embedding
        search_result = self.vector_store.query(query_embedding, similarity_top_k=top_k)

        return [
            {
                "text": node.get_content(),
                "score": node.score,
                "metadata": node.metadata
            }
            for node in search_result
        ]

    def clear(self):
        self.client.delete_collection(collection_name=settings.QDRANT_COLLECTION)
        self.client.create_collection(
            collection_name=settings.QDRANT_COLLECTION,
            vectors_config=qdrant_client.models.VectorParams(size=768, distance=qdrant_client.models.Distance.COSINE)
        )

# Dependency Injection point
_storage_instance = None

def get_vector_store() -> VectorStoreInterface:
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = QdrantStorage()
    return _storage_instance
