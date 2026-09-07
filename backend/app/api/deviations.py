from fastapi import APIRouter, HTTPException
from datetime import datetime
from backend.app.schemas.types import ReviewActionRequest, DeviationItem
from backend.app.core.job_runner import analyses_db

router = APIRouter(prefix="/api/deviations", tags=["Deviations"])

@router.post("/{analysis_id}/{deviation_id}/action", response_model=dict)
async def perform_review_action(
    analysis_id: str,
    deviation_id: str,
    action: ReviewActionRequest
):
    analysis = analyses_db.get(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    target_dev = None
    for dev in analysis.deviations:
        if dev.id == deviation_id:
            target_dev = dev
            break

    if not target_dev:
        raise HTTPException(status_code=404, detail="Deviation not found")

    target_dev.status = action.status
    if action.notes:
        target_dev.reviewer_notes = action.notes
    target_dev.reviewed_by = action.reviewer
    target_dev.reviewed_at = datetime.now()

    # Recalculate stats
    analysis.stats.confirmed_count = sum(1 for d in analysis.deviations if d.status.value == "CONFIRMED")
    analysis.stats.rejected_count = sum(1 for d in analysis.deviations if d.status.value == "REJECTED")
    analysis.stats.open_count = sum(1 for d in analysis.deviations if d.status.value == "OPEN")

    return {"status": "SUCCESS", "new_status": target_dev.status.value}
