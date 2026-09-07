import os
import shutil
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Optional

from backend.app.schemas.types import AnalysisDetail, AnalysisSummary
from backend.app.core.job_runner import job_runner, analyses_db
from backend.app.config import UPLOAD_DIR

router = APIRouter(prefix="/api/analyses", tags=["Analyses"])

@router.post("", response_model=dict)
async def create_analysis(
    pdf_file: UploadFile = File(...),
    config_file: UploadFile = File(...),
    project_name: str = Form("Industrial Control System"),
    pdf_revision: str = Form("Rev-0"),
    config_revision: str = Form("Rev-0"),
    parser_profile: str = Form("Generic"),
    api_key: Optional[str] = Form(None)
):
    pdf_path = os.path.join(str(UPLOAD_DIR), pdf_file.filename)
    config_path = os.path.join(str(UPLOAD_DIR), config_file.filename)

    with open(pdf_path, "wb") as f:
        shutil.copyfileobj(pdf_file.file, f)
    with open(config_path, "wb") as f:
        shutil.copyfileobj(config_file.file, f)

    job_id = job_runner.create_analysis_job(
        pdf_path=pdf_path,
        config_path=config_path,
        project_name=project_name,
        pdf_revision=pdf_revision,
        config_revision=config_revision,
        parser_profile=parser_profile,
        api_key=api_key
    )

    return {"job_id": job_id, "status": "QUEUED"}

@router.post("/demo", response_model=dict)
async def launch_demo_analysis():
    # Use one of the fixture files
    fixture_pdf_dir = r"C:\Users\karsa\Downloads\dktp pdf files"
    fixture_txt_dir = r"C:\Users\karsa\Downloads\dktp text files"

    pdf_sample = os.path.join(fixture_pdf_dir, "CP100R.pdf")
    txt_sample = os.path.join(fixture_txt_dir, "CP100R.txt")

    if not os.path.exists(pdf_sample) or not os.path.exists(txt_sample):
        # Fallback to any existing pdf/txt
        for f in os.listdir(fixture_pdf_dir):
            if f.endswith('.pdf'):
                pdf_sample = os.path.join(fixture_pdf_dir, f)
                break
        for f in os.listdir(fixture_txt_dir):
            if f.endswith('.txt'):
                txt_sample = os.path.join(fixture_txt_dir, f)
                break

    # Copy to uploads
    dest_pdf = os.path.join(str(UPLOAD_DIR), os.path.basename(pdf_sample))
    dest_cfg = os.path.join(str(UPLOAD_DIR), os.path.basename(txt_sample))
    shutil.copyfile(pdf_sample, dest_pdf)
    shutil.copyfile(txt_sample, dest_cfg)

    job_id = job_runner.create_analysis_job(
        pdf_path=dest_pdf,
        config_path=dest_cfg,
        project_name="Demo Power Plant Unit-1",
        pdf_revision="Rev.2A",
        config_revision="CP100R-Rev4",
        parser_profile="Foxboro / Schneider"
    )

    return {"job_id": job_id, "status": "QUEUED"}

@router.get("", response_model=List[AnalysisSummary])
async def list_analyses():
    return job_runner.list_analyses()

@router.get("/{analysis_id}", response_model=AnalysisDetail)
async def get_analysis_detail(analysis_id: str):
    analysis = job_runner.get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    return analysis
