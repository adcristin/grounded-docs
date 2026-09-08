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

    # 2. Ingestion
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
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # In a real app, log this properly
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
