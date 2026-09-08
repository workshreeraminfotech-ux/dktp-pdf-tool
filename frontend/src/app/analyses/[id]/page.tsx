'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  getAnalysis,
  getTextFileContent,
  getFileDownloadUrl,
  TextFileContentResponse
} from '@/lib/api';
import { AnalysisDetail, DeviationItem } from '@/types';
import {
  ArrowLeft,
  Download,
  FileText,
  FileCode,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  ChevronDown,
  Filter,
  RefreshCw,
  Table as TableIcon,
  Columns,
  Eye,
  Search,
  CheckCircle2,
  ExternalLink,
  Layers,
  FileSpreadsheet,
  ZoomIn,
  ZoomOut,
  Maximize2
} from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export default function CleanAnalysisWorkspace() {
  const params = useParams();
  const router = useRouter();
  const analysisId = params?.id as string;

  const [analysis, setAnalysis] = useState<AnalysisDetail | null>(null);
  const [textContent, setTextContent] = useState<TextFileContentResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedDeviation, setSelectedDeviation] = useState<DeviationItem | null>(null);
  const [filterOnlyMissing, setFilterOnlyMissing] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [activeTab, setActiveTab] = useState<'table' | 'split' | 'combined'>('table');
  const [searchQuery, setSearchQuery] = useState('');
  const [zoomLevel, setZoomLevel] = useState<number>(100);

  const lineRefs = useRef<Record<number, HTMLDivElement | null>>({});

  useEffect(() => {
    let timer: NodeJS.Timeout;

    const fetchAnalysis = async () => {
      if (!analysisId) return;
      try {
        const data = await getAnalysis(analysisId);
        setAnalysis(data);

        if (data.status === 'COMPLETED') {
          const txtData = await getTextFileContent(analysisId).catch(() => null);
          setTextContent(txtData);

          if (data.deviations && data.deviations.length > 0 && !selectedDeviation) {
            setSelectedDeviation(data.deviations[0]);
            setCurrentPage(data.deviations[0].page_number || 1);
          }
          setIsLoading(false);
        } else if (data.status === 'FAILED') {
          setIsLoading(false);
        } else {
          setIsLoading(true);
          timer = setTimeout(fetchAnalysis, 1500);
        }
      } catch (e) {
        console.error('Failed to load analysis:', e);
        setIsLoading(false);
      }
    };

    fetchAnalysis();

    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [analysisId]);

  // Scroll to selected line in text file
  useEffect(() => {
    if (selectedDeviation?.config_evidence?.line_start) {
      const lineNum = selectedDeviation.config_evidence.line_start;
      const el = lineRefs.current[lineNum];
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  }, [selectedDeviation]);

  const handleSelectDeviation = (dev: DeviationItem, switchToSplit: boolean = false) => {
    setSelectedDeviation(dev);
    setCurrentPage(dev.page_number || 1);
    setImageLoaded(false);
    if (switchToSplit) {
      setActiveTab('split');
    }
  };

  const deviatingLineNumbers = textContent?.deviations_by_line
    ? Object.keys(textContent.deviations_by_line).map(Number).sort((a, b) => a - b)
    : [];

  const handleNextMissingLine = () => {
    if (deviatingLineNumbers.length === 0 || !analysis) return;
    const currentLine = selectedDeviation?.config_evidence?.line_start || 0;
    const nextLine = deviatingLineNumbers.find((ln) => ln > currentLine) || deviatingLineNumbers[0];
    const devSummary = textContent?.deviations_by_line[nextLine]?.[0];
    if (devSummary) {
      const fullDev = analysis.deviations.find((d) => d.id === devSummary.id);
      if (fullDev) handleSelectDeviation(fullDev);
    }
  };

  const handlePrevMissingLine = () => {
    if (deviatingLineNumbers.length === 0 || !analysis) return;
    const currentLine = selectedDeviation?.config_evidence?.line_start || 999999;
    const prevLine =
      [...deviatingLineNumbers].reverse().find((ln) => ln < currentLine) ||
      deviatingLineNumbers[deviatingLineNumbers.length - 1];
    const devSummary = textContent?.deviations_by_line[prevLine]?.[0];
    if (devSummary) {
      const fullDev = analysis.deviations.find((d) => d.id === devSummary.id);
      if (fullDev) handleSelectDeviation(fullDev);
    }
  };

  // Loading state with real-time pipeline stages
  if (isLoading || (analysis && (analysis.status === 'QUEUED' || analysis.status === 'PROCESSING'))) {
    const stages = analysis?.stages || [];
    const activeStage = stages.find((s) => s.status === 'in_progress') || stages[0];
    const completedCount = stages.filter((s) => s.status === 'completed').length;
    const progressPercent = stages.length > 0 ? Math.round((completedCount / stages.length) * 100) : 15;

    return (
      <div className="min-h-screen bg-slate-50 text-slate-800 flex items-center justify-center p-6">
        <div className="text-center max-w-lg w-full bg-white border border-slate-200 rounded-2xl p-8 shadow-xl">
          <div className="w-12 h-12 border-3 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <h3 className="text-base font-bold text-slate-900 mb-1">
            AI Logic Audit in Progress...
          </h3>
          <p className="text-xs text-slate-500 mb-6 leading-relaxed">
            {activeStage?.description || 'Cross-checking engineering drawing blocks, timers, and DCS signals...'}
          </p>

          {/* Real-time Progress Bar */}
          <div className="w-full bg-slate-100 rounded-full h-2.5 mb-3 overflow-hidden border border-slate-200">
            <div
              className="bg-blue-600 h-2.5 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${Math.max(10, progressPercent)}%` }}
            />
          </div>

          <div className="flex items-center justify-between text-[11px] text-slate-500 font-semibold mb-6">
            <span>{activeStage?.details || 'Processing pipeline...'}</span>
            <span>{Math.max(10, progressPercent)}%</span>
          </div>

          <div className="p-3 bg-blue-50 border border-blue-200 rounded-xl text-left space-y-1.5 text-xs text-slate-700">
            <div className="flex items-center space-x-2 text-blue-900 font-bold">
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-blue-600" />
              <span>Pipeline Stage Active</span>
            </div>
            <p className="text-[11px] text-slate-600">
              Analyzing logic gates, setpoint thresholds, timer parameters (DON/TOF), and creating highlighted deviation table.
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (!analysis || analysis.status === 'FAILED') {
    return (
      <div className="min-h-screen bg-slate-50 text-slate-800 flex items-center justify-center p-6">
        <div className="text-center max-w-md bg-white border border-slate-200 rounded-2xl p-8 shadow-xl">
          <div className="w-12 h-12 rounded-full bg-red-100 text-red-600 flex items-center justify-center mx-auto mb-3">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-slate-900 mb-2">Analysis Failed or Not Found</h3>
          <p className="text-xs text-slate-500 mb-5">{analysis?.error_message || 'Could not load analysis results.'}</p>
          <button
            onClick={() => router.push('/')}
            className="px-4 py-2 rounded-xl bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 transition"
          >
            ← Back to Upload
          </button>
        </div>
      </div>
    );
  }

  const totalPages = analysis.stats.page_count || 1;
  const deviations = analysis.deviations || [];
  const textLines = textContent?.lines || [];

  const filteredDeviations = deviations.filter((d) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      d.block_name?.toLowerCase().includes(q) ||
      d.explanation?.toLowerCase().includes(q) ||
      d.equipment_tag?.toLowerCase().includes(q) ||
      d.page_number?.toString().includes(q)
    );
  });

  return (
    <div className="h-screen bg-slate-100 text-slate-900 flex flex-col font-sans overflow-hidden">
      {/* Top Header Bar */}
      <header className="border-b border-slate-200 bg-white px-6 py-2.5 flex items-center justify-between flex-shrink-0 shadow-xs z-20">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => router.push('/')}
            className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold flex items-center space-x-1.5 transition cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Upload New</span>
          </button>

          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-sm font-bold text-slate-900 truncate max-w-[300px]">
                {analysis.project_name}
              </h1>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-50 border border-red-200 text-red-700 flex items-center space-x-1">
                <AlertTriangle className="w-3.5 h-3.5 text-red-600" />
                <span>{deviations.length} Deviations Found</span>
              </span>
            </div>
            <p className="text-[11px] text-slate-500">
              PDF: <span className="font-semibold text-slate-700">{analysis.pdf_filename}</span> ({totalPages} Pages) &bull; TXT: <span className="font-semibold text-slate-700">{analysis.config_filename}</span>
            </p>
          </div>
        </div>

        {/* View Switcher Tabs */}
        <div className="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200">
          <button
            onClick={() => setActiveTab('table')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center space-x-1.5 transition ${
              activeTab === 'table'
                ? 'bg-white text-blue-700 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <TableIcon className="w-3.5 h-3.5" />
            <span>Deviation Table</span>
          </button>

          <button
            onClick={() => setActiveTab('split')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center space-x-1.5 transition ${
              activeTab === 'split'
                ? 'bg-white text-blue-700 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Columns className="w-3.5 h-3.5" />
            <span>Split View (PDF + TXT)</span>
          </button>

          <button
            onClick={() => setActiveTab('combined')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center space-x-1.5 transition ${
              activeTab === 'combined'
                ? 'bg-white text-blue-700 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Eye className="w-3.5 h-3.5" />
            <span>Combined</span>
          </button>
        </div>

        {/* Action Downloads */}
        <div className="flex items-center space-x-2">
          <a
            href={getFileDownloadUrl(analysis.id, 'annotated-txt')}
            download
            className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 border border-slate-200 text-slate-700 text-xs font-bold flex items-center space-x-1.5 transition shadow-xs"
          >
            <FileCode className="w-3.5 h-3.5 text-blue-600" />
            <span>Marked TXT</span>
            <Download className="w-3 h-3 text-slate-500" />
          </a>

          <a
            href={getFileDownloadUrl(analysis.id, 'report-xlsx')}
            download
            className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold flex items-center space-x-1.5 transition shadow-sm"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 text-white" />
            <span>Excel Export</span>
            <Download className="w-3 h-3 text-emerald-200" />
          </a>
        </div>
      </header>

      {/* Main Workspace Body */}
      <div className="flex-1 flex flex-col overflow-hidden p-3 gap-3">
        {/* ========================================================= */}
        {/* TAB 1: MASTER DEVIATION TABLE VIEW                        */}
        {/* ========================================================= */}
        {(activeTab === 'table' || activeTab === 'combined') && (
          <div
            className={`flex flex-col bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm ${
              activeTab === 'combined' ? 'h-1/2 flex-shrink-0' : 'flex-1'
            }`}
          >
            {/* Table Header Controls */}
            <div className="px-5 py-3 bg-white border-b border-slate-200 flex items-center justify-between flex-shrink-0">
              <div className="flex items-center space-x-2.5">
                <div className="w-6 h-6 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
                  <TableIcon className="w-3.5 h-3.5" />
                </div>
                <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Deviation Master Table
                </h2>
                <span className="text-[11px] font-semibold text-slate-500">
                  (Showing {filteredDeviations.length} of {deviations.length} items)
                </span>
              </div>

              {/* Search input */}
              <div className="flex items-center space-x-3">
                <div className="relative">
                  <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    placeholder="Search by Block or Keyword..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="bg-slate-50 border border-slate-200 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:bg-white w-64 transition"
                  />
                </div>
              </div>
            </div>

            {/* Table Content */}
            <div className="flex-1 overflow-auto">
              {filteredDeviations.length === 0 ? (
                <div className="p-12 text-center text-slate-400 text-xs">
                  No matching deviations found for your search.
                </div>
              ) : (
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-slate-50 text-slate-600 text-[11px] uppercase tracking-wider sticky top-0 border-b border-slate-200 font-bold z-10">
                    <tr>
                      <th className="py-3 px-4 w-28 text-center">PDF Page</th>
                      <th className="py-3 px-4 w-48">Deviation Tag</th>
                      <th className="py-3 px-6">Deviation Description</th>
                      <th className="py-3 px-6">Recommended Fix / Solution</th>
                      <th className="py-3 px-4 w-32 text-center">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {filteredDeviations.map((d, index) => {
                      const isSelected = selectedDeviation?.id === d.id;
                      return (
                        <tr
                          key={d.id || index}
                          onClick={() => handleSelectDeviation(d)}
                          className={`cursor-pointer transition duration-150 ${
                            isSelected
                              ? 'bg-blue-50/90 text-slate-900 border-l-4 border-l-blue-600'
                              : 'hover:bg-slate-50/80 text-slate-700'
                          }`}
                        >
                          {/* PDF Page No. Column */}
                          <td className="py-3.5 px-4 text-center align-top">
                            <span className="inline-flex items-center justify-center px-2.5 py-1 rounded-md text-xs font-bold bg-blue-50 border border-blue-200 text-blue-700 font-mono">
                              Page {d.page_number}
                            </span>
                          </td>

                          {/* Deviation (Block / Area) Column */}
                          <td className="py-3.5 px-4 font-mono font-bold text-slate-900 text-xs align-top">
                            <span className="text-amber-700 font-bold">{d.block_name || d.equipment_tag || 'DEVIATION'}</span>
                          </td>

                          {/* Deviation Description Column */}
                          <td className="py-3.5 px-6 text-slate-800 leading-relaxed text-xs align-top">
                            <p className="whitespace-normal font-sans">
                              {d.explanation}
                            </p>
                          </td>

                          {/* Deviation Solution Column */}
                          <td className="py-3.5 px-6 text-slate-800 leading-relaxed text-xs align-top">
                            <div className="flex items-start space-x-2 bg-emerald-50/80 p-2 rounded-lg border border-emerald-200/80">
                              <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
                              <span className="text-emerald-950 font-medium">{d.recommended_action || 'Update drawing schematic or DCS config to match specification.'}</span>
                            </div>
                          </td>

                          {/* Action Button Column */}
                          <td className="py-3.5 px-4 text-center align-top">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleSelectDeviation(d, true);
                              }}
                              className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-[11px] font-bold inline-flex items-center space-x-1.5 transition shadow-xs"
                            >
                              <span>Inspect Split</span>
                              <ExternalLink className="w-3 h-3" />
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}

        {/* ========================================================= */}
        {/* TAB 2 & 3: SPLIT SCREEN (DRAWING PDF + TEXT FILE)         */}
        {/* ========================================================= */}
        {(activeTab === 'split' || activeTab === 'combined') && (
          <div
            className={`flex gap-3 overflow-hidden ${
              activeTab === 'combined' ? 'h-1/2 flex-1' : 'flex-1'
            }`}
          >
            {/* LEFT PANEL: DRAWING PDF VIEWER (50%) */}
            <div className="w-1/2 h-full flex flex-col bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
              <div className="px-4 py-2.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between flex-shrink-0">
                <div className="flex items-center space-x-2">
                  <FileText className="w-4 h-4 text-blue-600" />
                  <span className="text-xs font-bold text-slate-900">Drawing PDF</span>
                  <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-white border border-slate-200 text-slate-600">
                    Page {currentPage} of {totalPages}
                  </span>
                </div>

                {/* Page Switcher & Zoom Controls */}
                <div className="flex items-center space-x-2">
                  <div className="flex items-center bg-white rounded-lg border border-slate-200 p-0.5 shadow-xs">
                    <button
                      onClick={() => setZoomLevel((z) => Math.max(50, z - 15))}
                      title="Zoom Out"
                      className="p-1 rounded hover:bg-slate-100 text-slate-600 transition"
                    >
                      <ZoomOut className="w-3.5 h-3.5" />
                    </button>
                    <span className="px-1.5 text-[10px] font-mono font-bold text-slate-600">{zoomLevel}%</span>
                    <button
                      onClick={() => setZoomLevel((z) => Math.min(200, z + 15))}
                      title="Zoom In"
                      className="p-1 rounded hover:bg-slate-100 text-slate-600 transition"
                    >
                      <ZoomIn className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  <div className="flex items-center space-x-1">
                    <button
                      disabled={currentPage <= 1}
                      onClick={() => {
                        setCurrentPage((p) => Math.max(1, p - 1));
                        setImageLoaded(false);
                      }}
                      className="px-2.5 py-1 rounded-lg bg-white hover:bg-slate-100 disabled:opacity-40 text-xs font-bold text-slate-700 border border-slate-200 flex items-center space-x-1 transition shadow-xs"
                    >
                      <ChevronLeft className="w-3.5 h-3.5" />
                      <span>Prev</span>
                    </button>

                    <button
                      disabled={currentPage >= totalPages}
                      onClick={() => {
                        setCurrentPage((p) => Math.min(totalPages, p + 1));
                        setImageLoaded(false);
                      }}
                      className="px-2.5 py-1 rounded-lg bg-white hover:bg-slate-100 disabled:opacity-40 text-xs font-bold text-slate-700 border border-slate-200 flex items-center space-x-1 transition shadow-xs"
                    >
                      <span>Next</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>

              {/* PDF Page Image Container */}
              <div className="flex-1 bg-slate-100/70 overflow-auto flex items-center justify-center p-4 relative">
                <div
                  style={{ transform: `scale(${zoomLevel / 100})`, transformOrigin: 'top center' }}
                  className="transition-transform duration-150 relative max-w-full bg-white rounded-lg shadow-md border border-slate-200 overflow-hidden flex items-center justify-center min-h-[350px]"
                >
                  <img
                    src={`${API_BASE}/api/files/page-image/${analysis.id}/${currentPage}`}
                    alt={`Drawing Page ${currentPage}`}
                    onLoad={() => setImageLoaded(true)}
                    className="max-w-full max-h-[72vh] object-contain block mx-auto"
                  />
                </div>
              </div>
            </div>

            {/* RIGHT PANEL: HIGHLIGHTED TEXT CONFIGURATION FILE (50%) */}
            <div className="w-1/2 h-full flex flex-col bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm font-mono text-xs">
              <div className="px-4 py-2.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between flex-shrink-0 font-sans">
                <div className="flex items-center space-x-2">
                  <FileCode className="w-4 h-4 text-emerald-600" />
                  <span className="text-xs font-bold text-slate-900 truncate max-w-[200px]">
                    {analysis.config_filename}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-50 text-red-700 border border-red-200">
                    {deviatingLineNumbers.length} Deviations
                  </span>
                </div>

                {/* Navigation & Filters */}
                <div className="flex items-center space-x-2">
                  <div className="flex items-center bg-white rounded-lg border border-slate-200 p-0.5 shadow-xs">
                    <button
                      onClick={handlePrevMissingLine}
                      title="Previous Missing Line"
                      className="p-1 rounded hover:bg-slate-100 text-slate-700 transition"
                    >
                      <ChevronUp className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={handleNextMissingLine}
                      title="Next Missing Line"
                      className="p-1 rounded hover:bg-slate-100 text-slate-700 transition"
                    >
                      <ChevronDown className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  <button
                    onClick={() => setFilterOnlyMissing(!filterOnlyMissing)}
                    className={`px-2.5 py-1 rounded-lg text-[11px] font-bold flex items-center space-x-1.5 transition border shadow-xs ${
                      filterOnlyMissing
                        ? 'bg-amber-100 text-amber-900 border-amber-300'
                        : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
                    }`}
                  >
                    <Filter className="w-3 h-3" />
                    <span>{filterOnlyMissing ? 'Showing Deviations' : 'Filter Deviations'}</span>
                  </button>
                </div>
              </div>

              {/* Text File Line-by-Line List */}
              <div className="flex-1 overflow-auto p-2 space-y-0.5 select-text bg-white">
                {textLines.length === 0 ? (
                  <div className="p-8 text-center text-slate-400 font-sans text-xs">
                    Loading configuration lines...
                  </div>
                ) : (
                  textLines.map((lineText, idx) => {
                    const lineNum = idx + 1;
                    const lineDevs = textContent?.deviations_by_line[lineNum] || [];
                    const hasDeviation = lineDevs.length > 0;
                    const isSelected = selectedDeviation?.config_evidence?.line_start === lineNum;

                    if (filterOnlyMissing && !hasDeviation) {
                      return null;
                    }

                    return (
                      <div
                        key={lineNum}
                        ref={(el) => {
                          lineRefs.current[lineNum] = el;
                        }}
                        onClick={() => {
                          if (hasDeviation) {
                            const fullDev = deviations.find((d) => d.id === lineDevs[0].id);
                            if (fullDev) handleSelectDeviation(fullDev);
                          }
                        }}
                        className={`rounded-lg px-2.5 py-1 transition-all ${
                          hasDeviation
                            ? isSelected
                              ? 'bg-red-50 border-l-4 border-red-600 text-red-950 ring-1 ring-red-400 shadow-xs cursor-pointer'
                              : 'bg-red-50/60 border-l-4 border-red-500 text-red-900 hover:bg-red-100/70 cursor-pointer'
                            : 'text-slate-600 hover:bg-slate-50'
                        }`}
                      >
                        <div className="flex items-start">
                          <span className="w-12 flex-shrink-0 text-slate-400 select-none text-right pr-3 text-[10px]">
                            {lineNum}
                          </span>
                          <span className="flex-1 whitespace-pre-wrap break-all font-mono">
                            {lineText || ' '}
                          </span>
                          {hasDeviation && (
                            <span className="ml-2 px-2 py-0.5 rounded text-[10px] font-bold bg-red-600 text-white flex-shrink-0 shadow-xs">
                              ⚠️ DEVIATION (P.{lineDevs[0].page_number})
                            </span>
                          )}
                        </div>

                        {hasDeviation && isSelected && (
                          <div className="mt-2 ml-12 p-3 rounded-lg bg-white border border-red-200 text-slate-800 font-sans shadow-md">
                            <div className="text-xs font-bold text-red-700 mb-1">
                              [{lineDevs[0].deviation_number}] {lineDevs[0].title}
                            </div>
                            <div className="text-[11px] text-slate-600 mb-1.5">
                              <strong className="text-slate-900">Issue:</strong> {lineDevs[0].explanation}
                            </div>
                            <div className="text-[11px] text-emerald-800 font-mono bg-emerald-50 px-2 py-1 rounded border border-emerald-200">
                              Drawing Page {lineDevs[0].page_number} Specification: &quot;{lineDevs[0].pdf_expected}&quot;
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
