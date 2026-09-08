from pydantic import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Grounded Docs"

    # Ollama Config
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "qwen3:4b"
    EMBED_MODEL: str = "embeddinggemma"

    # Qdrant Config
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "grounded_docs"

    # RAG Params
    RETRIEVAL_THRESHOLD: float = 0.7
    TOP_K_RETRIEVAL: int = 20  # Fetch more for the reranker
    TOP_K_RERANK: int = 5      # Pass only the best to the LLM
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    # Reranker Config
    RERANK_MODEL: str = "BAAI/bge-reranker-base"

    class Config:
        env_file = ".env"

settings = Settings()
