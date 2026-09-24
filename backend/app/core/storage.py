from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from llama_index.core import StorageContext, VectorStoreIndex, Settings
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
        import logging
        logger = logging.getLogger(__name__)

        embed_model = Settings.embed_model

        nodes = [
            TextNode(
                text=chunk["text"],
                id_=chunk.get("id"),
                metadata=chunk["metadata"]
            )
            for chunk in chunks
        ]

        try:
            # Log details of each chunk to identify potential trigger for crashes
            for i, node in enumerate(nodes):
                text = node.get_content()
                logger.info(f"Embedding chunk {i} | Length: {len(text)} chars | Preview: {text[:100]}...")

            # Manually embed the nodes individually to isolate batch issues
            embeddings = []
            for node in nodes:
                emb = embed_model.get_text_embedding(node.get_content())
                embeddings.append(emb)

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
        """Fully clear the collection by deleting and recreating it."""
        try:
            self.client.delete_collection(collection_name=settings.QDRANT_COLLECTION)
        except qdrant_client.http.exceptions.UnexpectedResponse as e:
            if "Not found" not in str(e):
                raise e

        self.client.create_collection(
            collection_name=settings.QDRANT_COLLECTION,
            vectors_config=qdrant_client.models.VectorParams(size=768, distance=qdrant_client.models.Distance.COSINE)
        )

    def get_status(self) -> Dict[str, Any]:
        """Returns the current point count and the filename of the active document."""
        try:
            collection_info = self.client.get_collection(collection_name=settings.QDRANT_COLLECTION)
            point_count = collection_info.points_count

            if point_count == 0:
                return {"active_document": None, "point_count": 0}

            # Retrieve the first point to get the source_filename from metadata
            points = self.client.scroll(
                collection_name=settings.QDRANT_COLLECTION,
                limit=1,
                with_payload=True
            )[0]

            filename = None
            if points:
                payload = points[0].payload
                filename = payload.get("source_filename")

            return {"active_document": filename, "point_count": point_count}
        except qdrant_client.http.exceptions.UnexpectedResponse as e:
            if "Not found" in str(e):
                return {"active_document": None, "point_count": 0}
            raise e
_storage_instance = None

def get_vector_store() -> VectorStoreInterface:
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = QdrantStorage()
    return _storage_instance
