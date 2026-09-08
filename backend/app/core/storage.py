from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from llama_index.core import StorageContext
from llama_index.vector_stores.qdrant import QdrantVectorStore
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
        # Note: LlamaIndex handles collection creation internally or via qdrant_client

    def add_chunks(self, chunks: List[Dict[str, Any]]):
        # LlamaIndex expects nodes. We'll convert the simplified chunk format back to nodes
        # if needed, or use the underlying vector_store's add method.
        # For now, we leverage the VectorStore's ability to add documents.

        from llama_index.core.schema import TextNode

        nodes = [
            TextNode(
                text=chunk["text"],
                id_=chunk.get("id"),
                metadata=chunk["metadata"]
            )
            for chunk in chunks
        ]
        self.vector_store.add(nodes)

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        # In a real implementation, we'd use the embedding model to query.
        # Since this is a storage interface, it might depend on an external embedder.
        # For this simplified architecture, we assume the VectorStore implementation
        # handles the embedding via its internal configuration.

        # This is a placeholder as LlamaIndex's VectorStore usually works
        # via a Retriever. We'll bridge this in the service layer.
        raise NotImplementedError("Retrieve logic is typically handled by the LlamaIndex Retriever using the VectorStore.")

    def clear(self):
        self.client.delete_collection(collection_name=settings.QDRANT_COLLECTION)
        self.client.create_collection(
            collection_name=settings.QDRANT_COLLECTION,
            vectors_config=qdrant_client.models.VectorParams(size=384, distance=qdrant_client.models.Distance.COSINE) # adjust size to embedder
        )

# Dependency Injection point
def get_vector_store() -> VectorStoreInterface:
    return QdrantStorage()
