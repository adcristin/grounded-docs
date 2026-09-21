# GroundedDocs

GroundedDocs lets you upload PDF or plain-text documents, ask questions, and receive grounded answers with source-mapped citations. Its core design principle is a **two-layer defense against hallucination**: a retrieval-level groundedness gate that blocks obviously irrelevant queries using a cross-encoder reranker score threshold, plus a strict generation-level prompt that refuses to answer when the retrieved chunk doesn't contain the actual fact asked—even if it passed the retrieval gate.

---

## Architecture

```
Upload
  → PyMuPDF text extraction
  → LlamaIndex SentenceSplitter chunking (chunk_size=500, overlap=50)
  → embeddinggemma embeddings (Ollama, local)
  → Qdrant vector store (COSINE, 768-dim)
  → top-k retrieval (k=20)
  → cross-encoder reranking (ms-marco-MiniLM-L-6-v2)
  → groundedness gate (reranker score ≥ -5.0)
  → qwen3:4b generation (Ollama, local) with strict context-only prompting
  → citation parsing ([n] markers → source filename + page)
  → response with citations
```
---

## Tech Stack

| Layer | Technology | Notes |
|-------|------------|-------|
| **Backend** | FastAPI | Python 3.11, uvicorn |
| **Frontend** | React 19 + Vite + TypeScript + Tailwind CSS 4 + shadcn/ui (Radix UI) | Three-pane layout: Chat, Source, Debug |
| **Vector Store** | Qdrant | Runs in Docker, COSINE distance, 768-dim vectors |
| **Embeddings** | `embeddinggemma` via Ollama | Local, no API key |
| **Generation** | `qwen3:4b` via Ollama | 
| **Reranker** | `sentence-transformers` CrossEncoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`) | Runs on CPU |
| **Orchestration** | LlamaIndex | Ingestion, indexing, retrieval, reranking |

**Entire pipeline runs locally at zero API cost — no external API keys required.**

---

## Setup & Running

### Prerequisites
- Docker & Docker Compose
- Ollama installed on the host with models pulled:
  ```bash
  ollama pull qwen3:4b
  ollama pull embeddinggemma
  ```

### Environment Variables
Create a `.env` file in the project root (or rely on defaults in `backend/app/core/config.py`):

| Variable | Default |
|----------|---------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` |
| `LLM_MODEL` | `qwen3:4b` |
| `EMBED_MODEL` | `embeddinggemma` |
| `QDRANT_URL` | `http://localhost:6333` |
| `QDRANT_COLLECTION` | `grounded_docs` |
| `RETRIEVAL_THRESHOLD` | `-5.0` |
| `TOP_K_RETRIEVAL` | `20` |
| `TOP_K_RERANK` | `5` |
| `CHUNK_SIZE` | `500` |
| `CHUNK_OVERLAP` | `50` |
| `RERANK_MODEL` | `cross-encoder/ms-marco-MiniLM-L-6-v2` |

> When running via Docker Compose, the API container uses `OLLAMA_BASE_URL=http://host.docker.internal:11434` and `QDRANT_URL=http://qdrant:6333` (set in `docker-compose.yml`).

### Start the Backend + Qdrant
```bash
docker compose up --build
```
- API: `http://localhost:8000`
- Qdrant dashboard: `http://localhost:6333/dashboard`

### Start the Frontend
```bash
cd frontend
npm install
npm run dev
```
- UI: `http://localhost:5173` (or the port Vite reports)

### Using the UI
1. **Upload a document** — Drag-and-drop or click to select a `.pdf` or `.txt` file. The UI shows chunk count and status.
2. **Ask a question** — Type your query in the chat pane. The answer appears with `[n]` citation markers.
3. **Inspect sources** — The **Source** pane shows the exact retrieved chunks with reranker scores, page numbers, and filenames.
4. **Debug details** — The **Debug** pane logs retrieval scores, reranker scores, and the groundedness gate decision.

---

## Design Decisions

### Chunking: SentenceSplitter (structure-aware, not semantic)
- **Settings**: `chunk_size=500`, `chunk_overlap=50` (from `config.py`).
- **Why not SemanticSplitterNodeParser?** Semantic splitting is slower, introduces an additional embedding model call per document, and adds complexity for marginal gains on technical documentation where paragraph boundaries already align with semantic units. SentenceSplitter is deterministic, fast, and preserves sentence integrity. Overlap mitigates boundary splits but doesn't eliminate them (see Limitations).

### Reranker on top of vector search
- Vector search (cosine similarity) retrieves a wide candidate set (top-20). The cross-encoder reranker (`ms-marco-MiniLM-L-6-v2`) scores query–chunk pairs with full attention, producing a **topical-relevance signal**—not a fact-presence signal.
- **Role**: Filter "best of the worst" results that cosine similarity promotes. It does **not** reliably distinguish "topically related but doesn't answer the question" from "actually contains the answer."

### Calibration findings (real sweep numbers)
| Category | Reranker score range | Notes |
|----------|---------------------|-------|
| **Positive** (answer present) | **-2.9 to +9.5** | Overlaps with hard negatives |
| **Hard negative** (topically related, answer absent) | **-0.5 to +5.8** | Overlaps with positives |
| **True negative** (completely unrelated) | **-11.0 to -11.2** | Clearly separated |

**Key takeaway**: The reranker score **alone cannot distinguish hard negatives from positives**. Their score distributions overlap substantially.

### Two-layer design (why not a single threshold?)
- The retrieval-level threshold (`RETRIEVAL_THRESHOLD = -5.0`) is **intentionally loose**—calibrated only to filter obvious irrelevance (true negatives). It lets through hard negatives because no safe single threshold separates them from positives.
- The **strict generation-level prompt** is the actual enforcement mechanism for fact-level grounding. It instructs the LLM to respond `"Insufficient context to answer the question."` when the retrieved chunks don't contain the fact, regardless of reranker score.
- This separation is more honest and robust: the reranker does what it's good at (topical filtering), the LLM does what it's good at (fact verification), and the system doesn't pretend a single scalar can do both.

---

## Known Limitations

1. **Chunk boundary splits** — A fact can be split across two chunks; 50-token overlap mitigates but doesn't eliminate this.
2. **Calibration scope** — Reranker calibration was validated on a **small single-chunk test document** (the NIST/cloud-computing fixture used in `validation_results.json`). Behavior on longer, multi-page corpora may differ.
3. **Local model quality** — `qwen3:4b` response quality is a step below larger hosted models.
4. **No OCR** — Only PDFs with extractable text and plain `.txt` files are supported. Scanned/image-only PDFs will fail extraction.
5. **Citation parsing** — The parser expects `[1]`, `[2]` numeric markers. If the LLM deviates (e.g., `[Source: ...]`), those citations won't be validated or linked in the Source pane.

---

## License

[MIT License](LICENSE) — Copyright (c) 2026 adcrisx