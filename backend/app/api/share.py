import uuid
from fastapi import APIRouter, HTTPException
from typing import Dict
from backend.app.schemas.types import AnalysisDetail
from backend.app.core.job_runner import analyses_db

router = APIRouter(prefix="/api/share", tags=["Share"])

share_tokens: Dict[str, str] = {} # token -> analysis_id

@router.post("/generate/{analysis_id}")
async def generate_share_link(analysis_id: str):
    if analysis_id not in analyses_db:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Look for existing token or create new
    for tok, aid in share_tokens.items():
        if aid == analysis_id:
            return {"token": tok, "share_url": f"/share/{tok}"}
    
    token = str(uuid.uuid4())[:12]
    share_tokens[token] = analysis_id
    return {"token": token, "share_url": f"/share/{token}"}

@router.get("/{token}", response_model=AnalysisDetail)
async def get_shared_analysis(token: str):
    analysis_id = share_tokens.get(token)
    if not analysis_id or analysis_id not in analyses_db:
        raise HTTPException(status_code=404, detail="Shared link is expired or invalid")
    return analyses_db[analysis_id]
