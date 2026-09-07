from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime

class SeverityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

class DeviationStatus(str, Enum):
    OPEN = "OPEN"
    UNDER_REVIEW = "UNDER_REVIEW"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"

class DeviationType(str, Enum):
    MISSING_SIGNAL = "MISSING_SIGNAL"
    EXTRA_SIGNAL = "EXTRA_SIGNAL"
    WRONG_SIGNAL_REF = "WRONG_SIGNAL_REF"
    WRONG_TAG = "WRONG_TAG"
    MISSING_INPUT = "MISSING_INPUT"
    MISSING_OUTPUT = "MISSING_OUTPUT"
    EXTRA_OUTPUT = "EXTRA_OUTPUT"
    SPARE_VS_CONFIGURED = "SPARE_VS_CONFIGURED"
    CONFIGURED_VS_SPARE = "CONFIGURED_VS_SPARE"
    LOGIC_DIFFERENCE = "LOGIC_DIFFERENCE"
    MISSING_LOGIC_BLOCK = "MISSING_LOGIC_BLOCK"
    EXTRA_LOGIC_BLOCK = "EXTRA_LOGIC_BLOCK"
    WRONG_BLOCK_REF = "WRONG_BLOCK_REF"
    TIMER_DIFFERENCE = "TIMER_DIFFERENCE"
    SETPOINT_DIFFERENCE = "SETPOINT_DIFFERENCE"
    TRIP_DIFFERENCE = "TRIP_DIFFERENCE"
    PERMISSIVE_DIFFERENCE = "PERMISSIVE_DIFFERENCE"
    INTERLOCK_DIFFERENCE = "INTERLOCK_DIFFERENCE"
    FEEDBACK_DIFFERENCE = "FEEDBACK_DIFFERENCE"
    STANDBY_DUTY_DIFFERENCE = "STANDBY_DUTY_DIFFERENCE"
    INVERSION_DIFFERENCE = "INVERSION_DIFFERENCE"
    DELAY_DEBOUNCE_DIFFERENCE = "DELAY_DEBOUNCE_DIFFERENCE"
    FIRST_OUT_DIFFERENCE = "FIRST_OUT_DIFFERENCE"
    SEQUENCE_DIFFERENCE = "SEQUENCE_DIFFERENCE"

class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class BoundingBox(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float
    width: Optional[float] = None
    height: Optional[float] = None

class PDFEvidence(BaseModel):
    file_name: str
    page_number: int
    coordinates: Optional[BoundingBox] = None
    extracted_text: str
    object_type: Optional[str] = "SIGNAL"
    snippet_url: Optional[str] = None

class ConfigEvidence(BaseModel):
    file_name: str
    line_start: int
    line_end: int
    block_name: Optional[str] = None
    parameter: Optional[str] = None
    value: str
    raw_snippet: Optional[str] = None

class DeviationItem(BaseModel):
    id: str
    deviation_number: str # e.g. DEV-001
    type: DeviationType
    severity: SeverityLevel
    status: DeviationStatus = DeviationStatus.OPEN
    page_number: int
    equipment_tag: Optional[str] = "GENERAL"
    block_name: Optional[str] = None
    pdf_expected: str
    config_actual: str
    explanation: str
    recommended_action: str
    confidence: int = Field(ge=0, le=100) # 0 - 100%
    confidence_level: str = "HIGH" # HIGH, MEDIUM, LOW
    is_root_cause: bool = True
    downstream_count: int = 0
    pdf_evidence: PDFEvidence
    config_evidence: ConfigEvidence
    reviewer_notes: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None

class AnalysisStats(BaseModel):
    total_deviations: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0
    review_required_count: int = 0
    confirmed_count: int = 0
    rejected_count: int = 0
    open_count: int = 0
    page_count: int = 0
    total_pdf_objects: int = 0
    total_config_objects: int = 0
    matched_objects: int = 0

class PipelineStage(BaseModel):
    name: str
    description: str
    status: str # "pending", "in_progress", "completed", "failed"
    progress: int = 0 # 0-100%
    details: Optional[str] = None

class AnalysisSummary(BaseModel):
    id: str
    project_id: Optional[str] = None
    project_name: Optional[str] = "Default Project"
    pdf_filename: str
    config_filename: str
    pdf_revision: Optional[str] = "Rev-0"
    config_revision: Optional[str] = "Rev-0"
    parser_profile: Optional[str] = "GENERIC"
    status: JobStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    stats: AnalysisStats
    stages: List[PipelineStage] = []

class AnalysisDetail(AnalysisSummary):
    deviations: List[DeviationItem] = []
    page_deviation_counts: Dict[int, int] = {}
    annotated_pdf_url: Optional[str] = None
    original_pdf_url: Optional[str] = None
    report_pdf_url: Optional[str] = None
    report_xlsx_url: Optional[str] = None
    report_csv_url: Optional[str] = None

class ReviewActionRequest(BaseModel):
    status: DeviationStatus
    notes: Optional[str] = None
    reviewer: Optional[str] = "Lead Engineer"

class TagAliasCreate(BaseModel):
    project_id: Optional[str] = "global"
    pdf_pattern: str
    config_pattern: str
    description: Optional[str] = None

class ParserProfile(BaseModel):
    id: str
    name: str
    vendor: str # "Generic", "Foxboro / Schneider", "ABB 800xA", "Siemens PCS7/TIA", "Emerson DeltaV", "Custom"
    description: str
    rules: Dict[str, Any] = {}
