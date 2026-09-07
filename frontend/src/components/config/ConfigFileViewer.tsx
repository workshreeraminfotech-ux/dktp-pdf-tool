'use client';

import React, { useState, useEffect, useRef } from 'react';
import { getTextFileContent, TextFileContentResponse, getFileDownloadUrl } from '@/lib/api';
import { DeviationItem } from '@/types';
import {
  FileText,
  AlertTriangle,
  Download,
  Filter,
  ChevronUp,
  ChevronDown,
  Search,
  CheckCircle2,
  ExternalLink,
  Code2
} from 'lucide-react';

interface ConfigFileViewerProps {
  analysisId: string;
  selectedDeviation: DeviationItem | null;
  onSelectDeviation: (dev: DeviationItem) => void;
  deviations: DeviationItem[];
}

export function ConfigFileViewer({
  analysisId,
  selectedDeviation,
  onSelectDeviation,
  deviations
}: ConfigFileViewerProps) {
  const [textContent, setTextContent] = useState<TextFileContentResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterOnlyDeviations, setFilterOnlyDeviations] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  
  const lineRefs = useRef<Record<number, HTMLDivElement | null>>({});
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (analysisId) {
      loadTextFile();
    }
  }, [analysisId]);

  const loadTextFile = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await getTextFileContent(analysisId);
      setTextContent(data);
    } catch (e: any) {
      console.error('Failed to load text file:', e);
      setError(e?.response?.data?.detail || 'Could not load configuration text file');
    } finally {
      setIsLoading(false);
    }
  };

  // Scroll to selected deviation line automatically
  useEffect(() => {
    if (selectedDeviation?.config_evidence?.line_number) {
      const lineNum = selectedDeviation.config_evidence.line_number;
      const el = lineRefs.current[lineNum];
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  }, [selectedDeviation]);

  const deviatingLineNumbers = textContent?.deviations_by_line
    ? Object.keys(textContent.deviations_by_line).map(Number).sort((a, b) => a - b)
    : [];

  const handleNextDeviation = () => {
    if (deviatingLineNumbers.length === 0) return;
    const currentLine = selectedDeviation?.config_evidence?.line_number || 0;
    const nextLine = deviatingLineNumbers.find((ln) => ln > currentLine) || deviatingLineNumbers[0];
    const devSummary = textContent?.deviations_by_line[nextLine]?.[0];
    if (devSummary) {
      const fullDev = deviations.find((d) => d.id === devSummary.id);
      if (fullDev) onSelectDeviation(fullDev);
    }
  };

  const handlePrevDeviation = () => {
    if (deviatingLineNumbers.length === 0) return;
    const currentLine = selectedDeviation?.config_evidence?.line_number || 999999;
    const prevLine = [...deviatingLineNumbers].reverse().find((ln) => ln < currentLine) || deviatingLineNumbers[deviatingLineNumbers.length - 1];
    const devSummary = textContent?.deviations_by_line[prevLine]?.[0];
    if (devSummary) {
      const fullDev = deviations.find((d) => d.id === devSummary.id);
      if (fullDev) onSelectDeviation(fullDev);
    }
  };

  if (isLoading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 text-slate-400 bg-slate-950">
        <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mb-3" />
        <p className="text-xs">Loading Configuration Text File & Highlighted Lines...</p>
      </div>
    );
  }

  if (error || !textContent) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 text-center bg-slate-950 text-slate-400">
        <FileText className="w-10 h-10 text-slate-600 mb-2" />
        <p className="text-xs font-semibold text-slate-300 mb-1">Configuration Text File</p>
        <p className="text-[11px] text-slate-500 max-w-xs">{error || 'No text configuration file available'}</p>
      </div>
    );
  }

  const lines = textContent.lines || [];

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-950 border-l border-slate-800 font-mono text-xs select-text overflow-hidden">
      {/* Top Toolbar */}
      <div className="flex items-center justify-between px-3 py-2 bg-slate-900/90 border-b border-slate-800 backdrop-blur-md flex-shrink-0">
        <div className="flex items-center space-x-2">
          <div className="p-1 rounded bg-cyan-950 border border-cyan-800 text-cyan-400">
            <Code2 className="w-3.5 h-3.5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-slate-200 text-xs font-sans truncate max-w-[180px]">
                {textContent.filename}
              </span>
              <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-red-950/80 border border-red-800/80 text-red-400">
                {deviatingLineNumbers.length} Deviating Lines
              </span>
            </div>
            <p className="text-[10px] text-slate-400 font-sans">
              Total {textContent.total_lines} lines &bull; Highlighted deviations
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center space-x-1.5">
          {/* Navigation between deviating lines */}
          <div className="flex items-center bg-slate-800/80 rounded border border-slate-700/60 p-0.5">
            <button
              onClick={handlePrevDeviation}
              title="Previous Deviating Line"
              className="p-1 rounded hover:bg-slate-700 text-slate-300 transition"
            >
              <ChevronUp className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={handleNextDeviation}
              title="Next Deviating Line"
              className="p-1 rounded hover:bg-slate-700 text-slate-300 transition"
            >
              <ChevronDown className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Toggle Filter Only Deviations */}
          <button
            onClick={() => setFilterOnlyDeviations(!filterOnlyDeviations)}
            className={`px-2 py-1 rounded text-[11px] font-sans font-medium flex items-center space-x-1 transition border ${
              filterOnlyDeviations
                ? 'bg-amber-950/80 text-amber-300 border-amber-700'
                : 'bg-slate-800/80 text-slate-300 border-slate-700 hover:bg-slate-700'
            }`}
          >
            <Filter className="w-3 h-3" />
            <span>{filterOnlyDeviations ? 'Showing Deviations' : 'Filter Deviations'}</span>
          </button>

          {/* Download Annotated TXT */}
          <a
            href={getFileDownloadUrl(analysisId, 'annotated-txt')}
            download
            className="px-2.5 py-1 rounded bg-cyan-600 hover:bg-cyan-500 text-white text-[11px] font-sans font-medium flex items-center space-x-1 transition shadow"
          >
            <Download className="w-3 h-3" />
            <span>Annotated TXT</span>
          </a>
        </div>
      </div>

      {/* Code / Text Lines Container */}
      <div
        ref={scrollContainerRef}
        className="flex-1 overflow-auto bg-slate-950 text-slate-300 p-2 space-y-0.5 font-mono text-[11px] leading-5"
      >
        {lines.map((lineText, idx) => {
          const lineNum = idx + 1;
          const lineDeviations = textContent.deviations_by_line[lineNum] || [];
          const hasDeviation = lineDeviations.length > 0;
          const isSelected = selectedDeviation?.config_evidence?.line_number === lineNum;

          if (filterOnlyDeviations && !hasDeviation) {
            return null;
          }

          // Severity colors for highlighted line
          const highestSeverity = lineDeviations[0]?.severity;
          let highlightClass = 'hover:bg-slate-900/60 text-slate-300';
          let borderClass = 'border-l-2 border-transparent';
          let badgeColor = 'bg-slate-800 text-slate-300';

          if (hasDeviation) {
            if (highestSeverity === 'CRITICAL') {
              highlightClass = 'bg-red-950/40 text-red-200';
              borderClass = 'border-l-4 border-red-500';
              badgeColor = 'bg-red-900/90 text-red-200 border-red-700';
            } else if (highestSeverity === 'HIGH') {
              highlightClass = 'bg-orange-950/40 text-orange-200';
              borderClass = 'border-l-4 border-orange-500';
              badgeColor = 'bg-orange-900/90 text-orange-200 border-orange-700';
            } else if (highestSeverity === 'MEDIUM') {
              highlightClass = 'bg-amber-950/40 text-amber-200';
              borderClass = 'border-l-4 border-amber-500';
              badgeColor = 'bg-amber-900/90 text-amber-200 border-amber-700';
            } else {
              highlightClass = 'bg-cyan-950/40 text-cyan-200';
              borderClass = 'border-l-4 border-cyan-500';
              badgeColor = 'bg-cyan-900/90 text-cyan-200 border-cyan-700';
            }
          }

          if (isSelected) {
            highlightClass += ' ring-1 ring-cyan-400 bg-cyan-950/60';
          }

          return (
            <div
              key={lineNum}
              ref={(el) => {
                lineRefs.current[lineNum] = el;
              }}
              className={`group transition-colors rounded-sm px-2 py-0.5 ${borderClass} ${highlightClass}`}
            >
              <div className="flex items-start">
                {/* Line Number */}
                <span className="w-12 flex-shrink-0 text-slate-500 select-none text-right pr-3 text-[10px]">
                  {lineNum}
                </span>

                {/* Code / Text Line */}
                <span className="flex-1 whitespace-pre-wrap break-all font-mono">
                  {lineText || ' '}
                </span>

                {/* Inline Badge for Deviating Lines */}
                {hasDeviation && (
                  <div className="flex items-center space-x-1 pl-2 flex-shrink-0">
                    {lineDeviations.map((dev) => (
                      <button
                        key={dev.id}
                        onClick={() => {
                          const fullDev = deviations.find((d) => d.id === dev.id);
                          if (fullDev) onSelectDeviation(fullDev);
                        }}
                        className={`px-1.5 py-0.2 rounded text-[9px] font-bold border flex items-center space-x-1 hover:brightness-125 transition ${badgeColor}`}
                        title={`Click to view on Drawing (Page ${dev.page_number})`}
                      >
                        <AlertTriangle className="w-2.5 h-2.5" />
                        <span>[{dev.deviation_number}]</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Expandable Explanation Banner when this line is selected */}
              {hasDeviation && isSelected && (
                <div className="mt-1.5 mb-1 ml-12 p-2.5 rounded-md bg-slate-900/95 border border-slate-700 text-slate-200 font-sans shadow-lg animate-in fade-in duration-200">
                  <div className="flex items-center justify-between pb-1.5 border-b border-slate-800 mb-2">
                    <div className="flex items-center space-x-2">
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-red-950 text-red-400 border border-red-800">
                        [{lineDeviations[0].deviation_number}] {lineDeviations[0].type}
                      </span>
                      <span className="text-[11px] font-semibold text-slate-300">
                        {lineDeviations[0].title}
                      </span>
                    </div>
                    <span className="text-[10px] text-cyan-400 font-mono">
                      Drawing Page: {lineDeviations[0].page_number}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-[11px] mb-2">
                    <div className="p-1.5 rounded bg-slate-950/80 border border-slate-800">
                      <span className="text-[10px] text-slate-400 font-mono block mb-0.5">
                        DRAWING EXPECTED:
                      </span>
                      <span className="font-mono text-emerald-400 font-semibold">
                        {lineDeviations[0].pdf_expected}
                      </span>
                    </div>
                    <div className="p-1.5 rounded bg-slate-950/80 border border-slate-800">
                      <span className="text-[10px] text-slate-400 font-mono block mb-0.5">
                        ACTUAL IN THIS LINE:
                      </span>
                      <span className="font-mono text-rose-400 font-semibold">
                        {lineDeviations[0].config_actual}
                      </span>
                    </div>
                  </div>

                  <p className="text-[11px] text-slate-400 leading-relaxed">
                    {lineDeviations[0].explanation}
                  </p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
