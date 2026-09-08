# Grounded Docs Project

A document-based Q&A assistant with strict grounding and citations.

## Tech Stack
- **Backend**: FastAPI, LlamaIndex, Qdrant, Ollama (local)
- **Frontend**: React, Vite, TypeScript, Tailwind, shadcn/ui
- **LLMs**: `embeddinggemma` (embeddings), `qwen3:4b/8b` (generation)

## Core Requirements
- Strict grounding: Answers must only use retrieved context.
- Thresholding: "Insufficient context" if retrieval confidence is low.
- Citations: Every claim must cite its source chunk.

## Development Workflow
- Local development via Docker Compose for Qdrant.
- Ollama running on host.
- Incremental implementation with educational insights.
