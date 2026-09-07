export type SeverityLevel = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';

export type DeviationStatus = 'OPEN' | 'UNDER_REVIEW' | 'CONFIRMED' | 'REJECTED';

export type DeviationType =
  | 'MISSING_SIGNAL'
  | 'EXTRA_SIGNAL'
  | 'WRONG_SIGNAL_REF'
  | 'WRONG_TAG'
  | 'MISSING_INPUT'
  | 'MISSING_OUTPUT'
  | 'EXTRA_OUTPUT'
  | 'SPARE_VS_CONFIGURED'
  | 'CONFIGURED_VS_SPARE'
  | 'LOGIC_DIFFERENCE'
  | 'MISSING_LOGIC_BLOCK'
  | 'EXTRA_LOGIC_BLOCK'
  | 'WRONG_BLOCK_REF'
  | 'TIMER_DIFFERENCE'
  | 'SETPOINT_DIFFERENCE'
  | 'TRIP_DIFFERENCE'
  | 'PERMISSIVE_DIFFERENCE'
  | 'INTERLOCK_DIFFERENCE'
  | 'FEEDBACK_DIFFERENCE'
  | 'STANDBY_DUTY_DIFFERENCE'
  | 'INVERSION_DIFFERENCE'
  | 'DELAY_DEBOUNCE_DIFFERENCE'
  | 'FIRST_OUT_DIFFERENCE'
  | 'SEQUENCE_DIFFERENCE';

export type JobStatus = 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'FAILED';

export interface BoundingBox {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
  width?: number;
  height?: number;
}

export interface PDFEvidence {
  file_name: string;
  page_number: number;
  coordinates?: BoundingBox;
  extracted_text: string;
  object_type?: string;
  snippet_url?: string;
}

export interface ConfigEvidence {
  file_name: string;
  line_start: number;
  line_end: number;
  line_number?: number;
  block_name?: string;
  parameter?: string;
  value: string;
  raw_snippet?: string;
}

export interface DeviationItem {
  id: string;
  deviation_number: string;
  type: DeviationType;
  severity: SeverityLevel;
  status: DeviationStatus;
  page_number: number;
  equipment_tag?: string;
  block_name?: string;
  pdf_expected: string;
  config_actual: string;
  explanation: string;
  recommended_action: string;
  confidence: number;
  confidence_level: string;
  is_root_cause: boolean;
  downstream_count: number;
  pdf_evidence: PDFEvidence;
  config_evidence: ConfigEvidence;
  reviewer_notes?: string;
  reviewed_by?: string;
  reviewed_at?: string;
}

export interface AnalysisStats {
  total_deviations: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  info_count: number;
  review_required_count: number;
  confirmed_count: number;
  rejected_count: number;
  open_count: number;
  page_count: number;
  total_pdf_objects: number;
  total_config_objects: number;
  matched_objects: number;
}

export interface PipelineStage {
  name: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  progress: number;
  details?: string;
}

export interface AnalysisSummary {
  id: string;
  project_id?: string;
  project_name?: string;
  pdf_filename: string;
  config_filename: string;
  pdf_revision?: string;
  config_revision?: string;
  parser_profile?: string;
  status: JobStatus;
  created_at: string;
  completed_at?: string;
  error_message?: string;
  stats: AnalysisStats;
  stages: PipelineStage[];
}

export interface AnalysisDetail extends AnalysisSummary {
  deviations: DeviationItem[];
  page_deviation_counts: Record<number, number>;
  annotated_pdf_url?: string;
  original_pdf_url?: string;
  report_pdf_url?: string;
  report_xlsx_url?: string;
  report_csv_url?: string;
}
