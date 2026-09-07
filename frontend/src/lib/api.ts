import axios from 'axios';
import { AnalysisDetail, AnalysisSummary, AnalysisStats } from '@/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export async function uploadAnalysis(formData: FormData): Promise<{ job_id: string; status: string }> {
  const res = await apiClient.post('/api/analyses', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
}

export async function startDemoAnalysis(): Promise<{ job_id: string; status: string }> {
  const res = await apiClient.post('/api/analyses/demo');
  return res.data;
}

export async function getAnalysis(id: string): Promise<AnalysisDetail> {
  const res = await apiClient.get<AnalysisDetail>(`/api/analyses/${id}`);
  return res.data;
}

export async function listAnalyses(): Promise<AnalysisSummary[]> {
  const res = await apiClient.get<AnalysisSummary[]>('/api/analyses');
  return res.data;
}

export async function updateDeviationStatus(
  analysisId: string,
  deviationId: string,
  status: string,
  notes?: string,
  reviewer: string = 'Control Systems Engineer'
) {
  const res = await apiClient.post(`/api/deviations/${analysisId}/${deviationId}/action`, {
    status,
    notes,
    reviewer,
  });
  return res.data;
}

export async function generateShareLink(analysisId: string): Promise<{ token: string; share_url: string }> {
  const res = await apiClient.post(`/api/share/generate/${analysisId}`);
  return res.data;
}

export async function getSharedAnalysis(token: string): Promise<AnalysisDetail> {
  const res = await apiClient.get<AnalysisDetail>(`/api/share/${token}`);
  return res.data;
}

export interface TextFileContentResponse {
  analysis_id: string;
  filename: string;
  total_lines: number;
  lines: string[];
  deviations_by_line: Record<number, Array<{
    id: string;
    deviation_number: string;
    type: string;
    severity: string;
    title: string;
    pdf_expected: string;
    config_actual: string;
    explanation: string;
    page_number: number;
  }>>;
}

export async function getTextFileContent(analysisId: string): Promise<TextFileContentResponse> {
  const res = await apiClient.get<TextFileContentResponse>(`/api/files/text-content/${analysisId}`);
  return res.data;
}

export function getFileDownloadUrl(analysisId: string, type: 'annotated' | 'original' | 'report-pdf' | 'report-xlsx' | 'report-csv' | 'annotated-txt') {
  return `${API_BASE}/api/files/download/${analysisId}/${type}`;
}
