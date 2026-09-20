import qdrant_client
from app.core.config import settings

client = qdrant_client.QdrantClient(url=settings.QDRANT_URL)
points = client.scroll(
    collection_name=settings.QDRANT_COLLECTION,
    limit=10,
    with_payload=True
)
print(points[0])
