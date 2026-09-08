import uuid
import fitz  # PyMuPDF
from typing import List, Dict, Any
from llama_index.core.node_parser import SentenceSplitter
from app.core.storage import VectorStoreInterface

class IngestionService:
    def __init__(self, storage: VectorStoreInterface, chunk_size: int = 500, chunk_overlap: int = 50):
        self.storage = storage
        self.splitter = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    def extract_text(self, filename: str, content: bytes) -> List[Dict[str, Any]]:
        """Extracts text from bytes, returning a list of (text, page_number) tuples."""
        extracted_pages = []

        if filename.endswith(".pdf"):
            doc = fitz.open(stream=content, filetype="pdf")
            for page_num, page in enumerate(doc, start=1):
                text = page.get_text().strip()
                if text:
                    extracted_pages.append({"text": text, "page": page_num})
            doc.close()
        elif filename.endswith(".txt"):
            text = content.decode("utf-8").strip()
            if text:
                extracted_pages.append({"text": text, "page": 1})
        else:
            raise ValueError("Unsupported file extension. Only .pdf and .txt are allowed.")

        if not extracted_pages:
            raise ValueError("No extractable text found in the document.")

        return extracted_pages

    async def process_and_store(self, filename: str, content: bytes):
        """Extracts, chunks, and stores the document."""
        # 1. Extract text
        pages = self.extract_text(filename, content)
        doc_id = str(uuid.uuid4())

        all_chunks = []
        chunk_global_index = 0

        # 2. Chunk each page (preserving page metadata)
        for page_data in pages:
            text = page_data["text"]
            page_num = page_data["page"]

            # LlamaIndex SentenceSplitter expects a string and returns a list of strings
            # though it usually operates on Documents. We can use it directly on text.
            chunks = self.splitter._split_text(text)

            for chunk_text in chunks:
                all_chunks.append({
                    "text": chunk_text,
                    "id": f"{doc_id}_{chunk_global_index}",
                    "metadata": {
                        "doc_id": doc_id,
                        "chunk_index": chunk_global_index,
                        "source_filename": filename,
                        "page_number": page_num
                    }
                })
                chunk_global_index += 1

        # 3. Store in vector store
        self.storage.add_chunks(all_chunks)

        return {
            "doc_id": doc_id,
            "total_chunks": len(all_chunks),
            "filename": filename
        }
