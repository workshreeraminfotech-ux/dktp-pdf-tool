import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.config import CORS_ORIGINS, SNIPPETS_DIR
from backend.app.api.analyses import router as analyses_router
from backend.app.api.deviations import router as deviations_router
from backend.app.api.files import router as files_router
from backend.app.api.share import router as share_router

app = FastAPI(
    title="Deviation Intelligence API",
    description="Automated Control-System Engineering Deviation Detection & PDF Highlighting Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyses_router)
app.include_router(deviations_router)
app.include_router(files_router)
app.include_router(share_router)

# Mount snippet files
app.mount("/static/snippets", StaticFiles(directory=str(SNIPPETS_DIR)), name="snippets")

@app.get("/api/health")
async def health_check():
    return {"status": "HEALTHY", "service": "Deviation Intelligence Core Engine"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
