'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { MetricsCards } from '@/components/deviation/MetricsCards';
import { ThumbnailList } from '@/components/pdf/ThumbnailList';
import { PdfViewer } from '@/components/pdf/PdfViewer';
import { DetailPanel } from '@/components/deviation/DetailPanel';
import { Table } from '@/components/deviation/Table';
import { getSharedAnalysis, updateDeviationStatus } from '@/lib/api';
import {
  AnalysisDetail,
  DeviationItem,
  SeverityLevel,
  DeviationStatus,
} from '@/types';
import { Layers, Lock } from 'lucide-react';

export default function SharedAnalysisPage() {
  const params = useParams();
  const router = useRouter();
  const token = params?.token as string;

  const [analysis, setAnalysis] = useState<AnalysisDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedDeviation, setSelectedDeviation] = useState<DeviationItem | null>(null);
  const [selectedSeverity, setSelectedSeverity] = useState<SeverityLevel | 'ALL' | 'REVIEW'>('ALL');

  useEffect(() => {
    if (token) {
      loadSharedData();
    }
  }, [token]);

  const loadSharedData = async () => {
    try {
      const data = await getSharedAnalysis(token);
      setAnalysis(data);
      if (data.deviations.length > 0) {
        setSelectedDeviation(data.deviations[0]);
        setCurrentPage(data.deviations[0].page_number);
      }
    } catch (e) {
      console.error('Failed to load shared analysis:', e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdateStatus = async (status: DeviationStatus, notes?: string) => {
    if (!analysis || !selectedDeviation) return;
    try {
      await updateDeviationStatus(analysis.id, selectedDeviation.id, status, notes);
      await loadSharedData();
    } catch (e) {
      alert('Failed to update status');
    }
  };

  const handleSelectDeviation = (dev: DeviationItem) => {
    setSelectedDeviation(dev);
    setCurrentPage(dev.page_number);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 text-slate-800 flex items-center justify-center">
        <div className="text-center">
          <div className="w-10 h-10 border-3 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-xs text-slate-500 font-medium">Loading Secure Audit Viewer...</p>
        </div>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="min-h-screen bg-slate-50 text-slate-800 flex flex-col items-center justify-center p-6 text-center">
        <div className="w-12 h-12 rounded-full bg-slate-200 flex items-center justify-center mx-auto mb-3 text-slate-600">
          <Lock className="w-6 h-6" />
        </div>
        <h3 className="text-lg font-bold text-slate-900">Secure Share Link Invalid or Expired</h3>
        <p className="text-xs text-slate-500 max-w-sm mt-1">
          This shared analysis link is no longer accessible. Please contact the project owner for a new link.
        </p>
      </div>
    );
  }

  const filteredDeviations = analysis.deviations.filter((d) => {
    if (selectedSeverity === 'ALL') return true;
    if (selectedSeverity === 'REVIEW') return d.confidence < 90;
    return d.severity === selectedSeverity;
  });

  return (
    <div className="h-screen bg-slate-100 text-slate-900 flex flex-col font-sans overflow-hidden">
      <header className="h-14 bg-white border-b border-slate-200 text-slate-800 flex items-center justify-between px-6 z-30 sticky top-0 shadow-xs">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center shadow-md shadow-blue-600/20 text-white">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <div className="font-bold text-sm text-slate-900 flex items-center gap-2">
              DKTP Logic Deviation Audit
              <span className="text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200 px-1.5 py-0.5 rounded">
                Secure Shared View
              </span>
            </div>
            <div className="text-[11px] text-slate-500">
              {analysis.project_name}
            </div>
          </div>
        </div>
      </header>

      <div className="flex-1 flex flex-col overflow-hidden p-4">
        <MetricsCards
          stats={analysis.stats}
          selectedSeverity={selectedSeverity}
          onSelectSeverity={setSelectedSeverity}
        />

        <div className="flex-1 flex rounded-xl border border-slate-200 overflow-hidden bg-white shadow-sm min-h-0">
          <ThumbnailList
            pageCount={analysis.stats.page_count || 1}
            currentPage={currentPage}
            pageDeviationCounts={analysis.page_deviation_counts || {}}
            onSelectPage={setCurrentPage}
          />

          <PdfViewer
            pdfUrl={analysis.original_pdf_url}
            annotatedPdfUrl={analysis.annotated_pdf_url}
            currentPage={currentPage}
            totalPages={analysis.stats.page_count || 1}
            deviations={filteredDeviations}
            selectedDeviation={selectedDeviation}
            onSelectDeviation={handleSelectDeviation}
            onPageChange={setCurrentPage}
          />

          <div className="w-96 flex-shrink-0 h-full">
            <DetailPanel
              deviation={selectedDeviation}
              onUpdateStatus={handleUpdateStatus}
            />
          </div>
        </div>

        <div className="mt-3 rounded-xl border border-slate-200 overflow-hidden shadow-sm">
          <Table
            deviations={filteredDeviations}
            selectedDeviation={selectedDeviation}
            onSelectDeviation={handleSelectDeviation}
            analysisId={analysis.id}
          />
        </div>
      </div>
    </div>
  );
}
