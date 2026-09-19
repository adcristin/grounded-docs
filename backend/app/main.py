from llama_index.core import Settings
from llama_index.embeddings.ollama import OllamaEmbedding
from app.core.config import settings

# Initialize Global Embedding Model at the very top to prevent import-order bugs
Settings.embed_model = OllamaEmbedding(
    model_name=settings.EMBED_MODEL,
    base_url=settings.OLLAMA_BASE_URL
)

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import upload, query
from app.core.storage import get_vector_store

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure Qdrant collection is created with correct config
    try:
        get_vector_store()
        print("Qdrant collection verified/created successfully.")
    except Exception as e:
        print(f"Critical error initializing Qdrant storage: {e}")
        # We don't raise here to allow the app to start,
        # but in a real prod app, you might want to fail fast.

    yield

app = FastAPI(title="Grounded Docs API", lifespan=lifespan)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router, prefix="/api", tags="Documents")
app.include_router(query.router, prefix="/api", tags="Query")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
