# Design Rationale: Grounded Docs

## Architecture Overview
Grounded Docs is a document-based Q&A assistant designed for high-fidelity grounding and transparency. It employs a "retrieve-rerank-generate" pipeline to minimize hallucinations and provide verifiable citations.

## Key Design Choices

### 1. Chunking Strategy
- **Chunk Size**: 500 tokens
- **Overlap**: 50 tokens
- **Rationale**: A 500-token window provides enough context for the LLM to generate a coherent answer while remaining small enough to ensure high retrieval precision. The 50-token overlap prevents the loss of semantic meaning at chunk boundaries.

### 2. Model Selection
- **Embedding Model**: `embeddinggemma`
  - **Rationale**: Chosen for its strong performance on local benchmarks and efficiency in creating dense vector representations of technical documentation.
- **Generation Models**: `qwen3:4b` and `qwen3:8b`
  - **Rationale**: Qwen3 models exhibit strong instruction-following and grounding capabilities. The choice between 4b and 8b allows users to trade off latency for quality:
    - `4b`: Faster, lower VRAM usage, suitable for simple factual retrieval.
    - `8b`: Better reasoning and nuance, higher quality citations.

### 3. Retrieval Thresholding (The Groundedness Gate)
- **Threshold**: 0.4 (Rerank Score)
- **Rationale**: After the initial retrieval, a cross-encoder reranker provides a more precise similarity score. A threshold of 0.4 was chosen empirically to filter out "best of the worst" results that often lead to hallucinations. When the top score is below this value, the system triggers the "Insufficient context" state rather than attempting to guess.

## Citation Mechanism
Every generated answer is parsed for `[n]` markers. These markers are validated against the retrieved candidates. If a marker does not map to a valid chunk, it is treated as a hallucination and rendered as plain text in the UI to maintain transparency.

## UI/UX Design
The three-pane layout (Chat, Source, Debug) is designed to move the system from a "black box" to a "glass box." By surfacing the exact chunk and the similarity scores, users can audit the AI's reasoning process in real-time.
