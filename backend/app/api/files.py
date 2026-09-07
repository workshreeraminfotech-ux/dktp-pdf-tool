import os
import pymupdf
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.app.config import PROCESSED_DIR, REPORTS_DIR, SNIPPETS_DIR, UPLOAD_DIR
from backend.app.core.job_runner import analyses_db

router = APIRouter(prefix="/api/files", tags=["Files"])

@router.get("/download/{analysis_id}/annotated")
async def download_annotated_pdf(analysis_id: str):
    file_path = os.path.join(str(PROCESSED_DIR), f"annotated_{analysis_id}.pdf")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Annotated PDF not found")
    return FileResponse(file_path, media_type="application/pdf", filename=f"annotated_{analysis_id}.pdf")

@router.get("/download/{analysis_id}/original")
async def download_original_pdf(analysis_id: str):
    analysis = analyses_db.get(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    file_path = os.path.join(str(UPLOAD_DIR), analysis.pdf_filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Original PDF not found")
    return FileResponse(file_path, media_type="application/pdf", filename=analysis.pdf_filename)

@router.get("/download/{analysis_id}/report-pdf")
async def download_report_pdf(analysis_id: str):
    file_path = os.path.join(str(REPORTS_DIR), f"report_{analysis_id}.pdf")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="PDF Audit Report not found")
    return FileResponse(file_path, media_type="application/pdf", filename=f"audit_report_{analysis_id}.pdf")

@router.get("/download/{analysis_id}/report-xlsx")
async def download_report_xlsx(analysis_id: str):
    file_path = os.path.join(str(REPORTS_DIR), f"report_{analysis_id}.xlsx")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Excel Report not found")
    return FileResponse(file_path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=f"deviations_{analysis_id}.xlsx")

@router.get("/download/{analysis_id}/report-csv")
async def download_report_csv(analysis_id: str):
    file_path = os.path.join(str(REPORTS_DIR), f"report_{analysis_id}.csv")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="CSV Report not found")
    return FileResponse(file_path, media_type="text/csv", filename=f"deviations_{analysis_id}.csv")

@router.get("/page-image/{analysis_id}/{page_num}")
async def get_page_image(analysis_id: str, page_num: int):
    file_path = os.path.join(str(PROCESSED_DIR), f"page_annotated_{analysis_id}_{page_num}.png")
    if not os.path.exists(file_path):
        # Check if original exists or render on demand
        analysis = analyses_db.get(analysis_id)
        if analysis:
            orig_path = os.path.join(str(UPLOAD_DIR), analysis.pdf_filename)
            if os.path.exists(orig_path):
                doc = pymupdf.open(orig_path)
                if 0 <= (page_num - 1) < len(doc):
                    page = doc[page_num - 1]
                    pix = page.get_pixmap(dpi=144)
                    pix.save(file_path)
                    doc.close()
                    return FileResponse(file_path, media_type="image/png")
                doc.close()
        raise HTTPException(status_code=404, detail="Page image not found")
    return FileResponse(file_path, media_type="image/png")

@router.get("/snippets/{filename}")
async def get_snippet_image(filename: str):
    file_path = os.path.join(str(SNIPPETS_DIR), filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Snippet image not found")
    return FileResponse(file_path, media_type="image/png")

@router.get("/text-content/{analysis_id}")
async def get_text_file_content(analysis_id: str):
    analysis = analyses_db.get(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    config_file_path = os.path.join(str(UPLOAD_DIR), analysis.config_filename)
    if not os.path.exists(config_file_path):
        raise HTTPException(status_code=404, detail="Configuration file not found on disk")
    
    try:
        with open(config_file_path, "r", encoding="utf-8", errors="replace") as f:
            raw_lines = f.readlines()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read configuration file: {e}")
    
    # Map deviations by line number (1-indexed)
    deviations_by_line = {}
    for dev in analysis.deviations:
        ln = dev.config_evidence.line_start
        if ln and ln > 0:
            deviations_by_line.setdefault(ln, []).append({
                "id": dev.id,
                "deviation_number": dev.deviation_number,
                "type": dev.type.value if hasattr(dev.type, "value") else str(dev.type),
                "severity": dev.severity.value if hasattr(dev.severity, "value") else str(dev.severity),
                "title": f"[{dev.deviation_number}] {dev.type.value if hasattr(dev.type, 'value') else str(dev.type)}",
                "pdf_expected": dev.pdf_expected,
                "config_actual": dev.config_actual,
                "explanation": dev.explanation,
                "page_number": dev.page_number
            })
    
    return {
        "analysis_id": analysis_id,
        "filename": analysis.config_filename,
        "total_lines": len(raw_lines),
        "lines": [line.rstrip("\r\n") for line in raw_lines],
        "deviations_by_line": deviations_by_line
    }

@router.get("/download/{analysis_id}/annotated-txt")
async def download_annotated_text_file(analysis_id: str):
    analysis = analyses_db.get(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    config_file_path = os.path.join(str(UPLOAD_DIR), analysis.config_filename)
    if not os.path.exists(config_file_path):
        raise HTTPException(status_code=404, detail="Configuration file not found on disk")
    
    # Read original lines
    with open(config_file_path, "r", encoding="utf-8", errors="replace") as f:
        raw_lines = f.readlines()
    
    # Map deviations by line
    devs_by_line = {}
    for dev in analysis.deviations:
        ln = dev.config_evidence.line_start
        if ln and ln > 0:
            devs_by_line.setdefault(ln, []).append(dev)
    
    # Build annotated file content
    annotated_output_path = os.path.join(str(PROCESSED_DIR), f"annotated_{analysis_id}.txt")
    with open(annotated_output_path, "w", encoding="utf-8") as out:
        out.write(f"# =============================================================================\n")
        out.write(f"# DEVIATION INTELLIGENCE - ANNOTATED AUDIT CONFIGURATION FILE\n")
        out.write(f"# Project: {analysis.project_name}\n")
        out.write(f"# Original File: {analysis.config_filename}\n")
        out.write(f"# Total Deviations Flagged: {len(analysis.deviations)}\n")
        out.write(f"# =============================================================================\n\n")
        
        for idx, line in enumerate(raw_lines):
            line_num = idx + 1
            out.write(line)
            if line_num in devs_by_line:
                for d in devs_by_line[line_num]:
                    sev = d.severity.value if hasattr(d.severity, "value") else str(d.severity)
                    dtype = d.type.value if hasattr(d.type, "value") else str(d.type)
                    out.write(f"    >>> [DEVIATION {d.deviation_number}] [{sev.upper()}] {dtype} <<<\n")
                    out.write(f"        DRAWING EXPECTED (P.{d.page_number}): {d.pdf_expected}\n")
                    out.write(f"        ACTUAL IN CONFIG: {d.config_actual}\n")
                    out.write(f"        REASON: {d.explanation}\n\n")

    return FileResponse(annotated_output_path, media_type="text/plain", filename=f"annotated_{analysis.config_filename}")
