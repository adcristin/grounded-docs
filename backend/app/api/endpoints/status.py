from fastapi import APIRouter, Depends, HTTPException
from app.core.storage import VectorStoreInterface, get_vector_store
from typing import Dict, Any

router = APIRouter()

@router.get("/status")
async def get_status(storage: VectorStoreInterface = Depends(get_vector_store)) -> Dict[str, Any]:
    """Returns the status of the current active document."""
    return storage.get_status()

@router.post("/clear")
async def clear_collection(storage: VectorStoreInterface = Depends(get_vector_store)):
    """Manually clears the current collection."""
    try:
        storage.clear()
        return {"status": "success", "message": "Collection cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear collection: {str(e)}")
