from fastapi import FastAPI
from app.api.endpoints import upload, query

app = FastAPI(title="Grounded Docs API")

# Include routers
app.include_router(upload.router, prefix="/api", tags=["Documents"])
app.include_router(query.router, prefix="/api", tags=["Query"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
