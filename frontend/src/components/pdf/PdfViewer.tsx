'use client';

import React, { useState, useRef, useEffect } from 'react';
import { DeviationItem, SeverityLevel } from '@/types';
import {
  ZoomIn,
  ZoomOut,
  Maximize2,
  ChevronLeft,
  ChevronRight,
  Download,
  Layers,
  Eye,
  AlertTriangle,
  RotateCcw,
} from 'lucide-react';

interface PdfViewerProps {
  pdfUrl?: string;
  annotatedPdfUrl?: string;
  currentPage: number;
  totalPages: number;
  deviations: DeviationItem[];
  selectedDeviation: DeviationItem | null;
  onSelectDeviation: (dev: DeviationItem) => void;
  onPageChange: (page: number) => void;
  onNextDeviation?: () => void;
  onPrevDeviation?: () => void;
}

export const PdfViewer: React.FC<PdfViewerProps> = ({
  pdfUrl,
  annotatedPdfUrl,
  currentPage,
  totalPages,
  deviations,
  selectedDeviation,
  onSelectDeviation,
  onPageChange,
  onNextDeviation,
  onPrevDeviation,
}) => {
  const [zoom, setZoom] = useState(1.0);
  const [showAnnotations, setShowAnnotations] = useState(true);
  const containerRef = useRef<HTMLDivElement>(null);

  // Filter deviations on the current page
  const pageDeviations = deviations.filter((d) => d.page_number === currentPage);

  const getSeverityColor = (sev: SeverityLevel) => {
    switch (sev) {
      case 'CRITICAL':
        return { stroke: '#DC2626', fill: 'rgba(220, 38, 38, 0.15)', badge: 'bg-red-600' };
      case 'HIGH':
        return { stroke: '#EA580C', fill: 'rgba(234, 88, 12, 0.15)', badge: 'bg-amber-600' };
      case 'MEDIUM':
        return { stroke: '#CA8A04', fill: 'rgba(202, 138, 4, 0.15)', badge: 'bg-yellow-600' };
      case 'LOW':
        return { stroke: '#2563EB', fill: 'rgba(37, 99, 235, 0.15)', badge: 'bg-blue-600' };
      default:
        return { stroke: '#64748B', fill: 'rgba(100, 116, 139, 0.15)', badge: 'bg-slate-600' };
    }
  };

  // Base canvas standard A4 landscape points (842 x 595)
  const baseWidth = 842;
  const baseHeight = 595;

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-950 text-white select-none overflow-hidden">
      {/* Top Controls Toolbar */}
      <div className="h-12 bg-slate-900 border-b border-slate-800 px-4 flex items-center justify-between text-xs">
        {/* Page Navigation */}
        <div className="flex items-center space-x-2">
          <button
            disabled={currentPage <= 1}
            onClick={() => onPageChange(currentPage - 1)}
            className="p-1 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 transition-colors"
            title="Previous Page"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="font-semibold text-slate-300">
            Page {currentPage} of {totalPages || 1}
          </span>
          <button
            disabled={currentPage >= totalPages}
            onClick={() => onPageChange(currentPage + 1)}
            className="p-1 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 transition-colors"
            title="Next Page"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        {/* Deviation Stepper */}
        <div className="flex items-center space-x-2">
          {onPrevDeviation && onNextDeviation && (
            <div className="flex items-center space-x-1 bg-slate-800 p-0.5 rounded border border-slate-700">
              <button
                onClick={onPrevDeviation}
                className="px-2 py-1 rounded text-slate-300 hover:text-white hover:bg-slate-700 text-[11px] font-medium"
              >
                &larr; Prev Dev
              </button>
              <span className="text-slate-500 text-[10px]">|</span>
              <button
                onClick={onNextDeviation}
                className="px-2 py-1 rounded text-slate-300 hover:text-white hover:bg-slate-700 text-[11px] font-medium"
              >
                Next Dev &rarr;
              </button>
            </div>
          )}

          <button
            onClick={() => setShowAnnotations(!showAnnotations)}
            className={`flex items-center space-x-1 px-2.5 py-1 rounded border text-[11px] font-medium transition-colors ${
              showAnnotations
                ? 'bg-cyan-950 border-cyan-700 text-cyan-300'
                : 'bg-slate-800 border-slate-700 text-slate-400'
            }`}
          >
            <Eye className="w-3.5 h-3.5" />
            <span>Highlights {showAnnotations ? 'ON' : 'OFF'}</span>
          </button>
        </div>

        {/* Zoom Controls */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setZoom((z) => Math.max(0.5, z - 0.15))}
            className="p-1 rounded bg-slate-800 hover:bg-slate-700 transition-colors"
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <span className="w-12 text-center font-mono font-medium text-slate-300">
            {Math.round(zoom * 100)}%
          </span>
          <button
            onClick={() => setZoom((z) => Math.min(2.5, z + 0.15))}
            className="p-1 rounded bg-slate-800 hover:bg-slate-700 transition-colors"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={() => setZoom(1.0)}
            className="p-1 rounded bg-slate-800 hover:bg-slate-700 transition-colors"
            title="Reset Zoom"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Main Drawing Canvas / Embedded Frame Area */}
      <div
        ref={containerRef}
        className="flex-1 overflow-auto p-6 flex items-center justify-center bg-slate-950 relative"
      >
        <div
          className="relative bg-white shadow-2xl rounded border border-slate-700 transition-transform origin-center"
          style={{
            width: `${baseWidth * zoom}px`,
            height: `${baseHeight * zoom}px`,
            minWidth: `${baseWidth * zoom}px`,
            minHeight: `${baseHeight * zoom}px`,
          }}
        >
          {/* High-Resolution Page Drawing Canvas */}
          <div className="w-full h-full relative overflow-hidden bg-slate-100 dark:bg-slate-900 rounded">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={
                annotatedPdfUrl
                  ? `http://127.0.0.1:8000/api/files/page-image/${annotatedPdfUrl.split('/')[4]}/${currentPage}`
                  : ''
              }
              alt={`Drawing Page ${currentPage}`}
              className="w-full h-full object-contain pointer-events-none"
              onError={(e) => {
                // Fallback to iframe if page-image is loading
                (e.target as HTMLElement).style.display = 'none';
              }}
            />
          </div>

          {/* Interactive Clickable Highlight Overlay Layer */}
          {showAnnotations && (
            <svg
              className="absolute inset-0 w-full h-full pointer-events-none"
              viewBox={`0 0 ${baseWidth} ${baseHeight}`}
            >
              {pageDeviations.map((dev) => {
                const coords = dev.pdf_evidence.coordinates;
                if (!coords) return null;

                const isSelected = selectedDeviation?.id === dev.id;
                const colors = getSeverityColor(dev.severity);

                const x = coords.x0;
                const y = coords.y0;
                const width = Math.max(25, coords.x1 - coords.x0);
                const height = Math.max(16, coords.y1 - coords.y0);

                return (
                  <g
                    key={dev.id}
                    className="pointer-events-auto cursor-pointer group"
                    onClick={() => onSelectDeviation(dev)}
                  >
                    {/* Bounding Box Highlight */}
                    <rect
                      x={x - 2}
                      y={y - 2}
                      width={width + 4}
                      height={height + 4}
                      fill={colors.fill}
                      stroke={colors.stroke}
                      strokeWidth={isSelected ? 3 : 1.8}
                      rx={3}
                      className="transition-all group-hover:stroke-white group-hover:stroke-2"
                    />

                    {/* Badge Label Tag */}
                    <rect
                      x={x - 2}
                      y={Math.max(4, y - 16)}
                      width={48}
                      height={13}
                      fill={colors.stroke}
                      rx={2}
                    />
                    <text
                      x={x + 2}
                      y={Math.max(13, y - 6)}
                      fill="#FFFFFF"
                      fontSize="9"
                      fontWeight="bold"
                      fontFamily="sans-serif"
                    >
                      {dev.deviation_number}
                    </text>
                  </g>
                );
              })}
            </svg>
          )}
        </div>
      </div>
    </div>
  );
};
