from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.services.ingestion import IngestionService
from app.core.storage import VectorStoreInterface, get_vector_store
from app.core.config import settings

router = APIRouter()

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    storage: VectorStoreInterface = Depends(get_vector_store)
):
    # 1. Basic Validation
    if file.filename == "":
        raise HTTPException(status_code=400, detail="Filename is missing")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="File is empty")

    # 2. Atomic Reset and Ingestion
    # We clear the collection first to ensure only one document is active.
    # This implements the global clear-on-upload requirement.
    try:
        storage.clear()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear existing collection: {str(e)}")

    service = IngestionService(
        storage=storage,
        chunk_size=settings.CHUNK_SIZE if hasattr(settings, 'CHUNK_SIZE') else 500,
        chunk_overlap=settings.CHUNK_OVERLAP if hasattr(settings, 'CHUNK_OVERLAP') else 50
    )

    try:
        result = await service.process_and_store(file.filename, content)
        return {
            "status": "success",
            "message": f"Document {file.filename} processed successfully",
            "data": result
        }
    except ValueError as e:
        # If extraction fails, the collection is already cleared, which is the desired state.
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Log that the ingestion failed and the collection is left empty.
        # In a real app, use a proper logger here.
        print(f"Ingestion failed for {file.filename}: {str(e)}. Collection left empty.")
        raise HTTPException(status_code=500, detail=f"Internal server error during ingestion: {str(e)}")
