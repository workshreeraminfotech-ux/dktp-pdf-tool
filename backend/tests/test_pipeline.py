import pytest
import os
from backend.app.core.parser.normalizer import TagNormalizer
from backend.app.core.parser.config_parser import UniversalConfigParser
from backend.app.core.parser.pdf_parser import PDFUnderstandingEngine
from backend.app.core.engine.deviation_engine import IndustrialDeviationEngine
from backend.app.core.engine.annotator import PDFVisualAnnotator
from backend.app.core.engine.report_generator import AuditReportGenerator
from backend.app.schemas.types import SeverityLevel, DeviationType, AnalysisSummary, AnalysisStats, PipelineStage, JobStatus
from datetime import datetime

def test_normalizer():
    norm = TagNormalizer({"PUMP_RUN_OLD": "PUMP_RUN_NEW"})
    assert norm.normalize("U10PDI:DIR38125.CIN") == "DIR38125"
    assert norm.normalize("10PAB50AP001.BO07") == "10PAB50AP001"
    assert norm.normalize("PUMP_RUN_OLD") == "PUMP_RUN_NEW"
    assert norm.is_spare_or_unused("0") is True
    assert norm.is_spare_or_unused("SPARE") is True
    assert norm.is_spare_or_unused("DIR38125") is False
    assert norm.classify_semantics("OPERATOR STANDBY SELECTED") == "STANDBY"
    assert norm.classify_semantics("MOTOR_TRIP_FB") == "TRIP"

def test_config_parser():
    txt_path = r"C:\Users\karsa\Downloads\dktp text files\CP100R.txt"
    if os.path.exists(txt_path):
        parser = UniversalConfigParser()
        result = parser.parse_file(txt_path)
        assert len(result.blocks) > 0
        assert result.total_lines > 1000
        assert len(result.all_signals) > 0

def test_full_pipeline_on_fixtures(tmp_path):
    pdf_path = r"C:\Users\karsa\Downloads\dktp pdf files\CP100R.pdf"
    txt_path = r"C:\Users\karsa\Downloads\dktp text files\CP100R.txt"

    if os.path.exists(pdf_path) and os.path.exists(txt_path):
        normalizer = TagNormalizer()
        pdf_engine = PDFUnderstandingEngine(normalizer)
        config_parser = UniversalConfigParser(normalizer)
        deviation_engine = IndustrialDeviationEngine(normalizer)
        annotator = PDFVisualAnnotator()
        report_gen = AuditReportGenerator()

        # 1. Parse PDF
        pdf_pages = pdf_engine.process_pdf(pdf_path, max_pages=5)
        assert len(pdf_pages) == 5

        # 2. Parse Config
        config_file = config_parser.parse_file(txt_path)
        assert len(config_file.blocks) > 0

        # 3. Detect Deviations
        deviations = deviation_engine.detect_deviations(pdf_pages, config_file)
        assert len(deviations) >= 0

        # 4. Annotate PDF
        out_pdf = str(tmp_path / "annotated.pdf")
        annotator.annotate_pdf(pdf_path, out_pdf, deviations, generate_snippets=False)
        assert os.path.exists(out_pdf)

        # 5. Generate Reports
        summary = AnalysisSummary(
            id="test-job-001",
            pdf_filename="CP100R.pdf",
            config_filename="CP100R.txt",
            status=JobStatus.COMPLETED,
            created_at=datetime.now(),
            stats=AnalysisStats(total_deviations=len(deviations), page_count=len(pdf_pages))
        )
        out_report_pdf = str(tmp_path / "report.pdf")
        out_report_xlsx = str(tmp_path / "report.xlsx")
        report_gen.generate_pdf_report(summary, deviations, out_report_pdf)
        report_gen.generate_excel_report(summary, deviations, out_report_xlsx)
        assert os.path.exists(out_report_pdf)
        assert os.path.exists(out_report_xlsx)
