'use client';

import React, { useState } from 'react';
import { DeviationItem, SeverityLevel, DeviationStatus } from '@/types';
import {
  CheckCircle,
  XCircle,
  HelpCircle,
  MessageSquare,
  ExternalLink,
  ShieldAlert,
  ArrowRight,
  FileCode,
  FileSearch,
  Check,
  Sparkles,
} from 'lucide-react';

interface DetailPanelProps {
  deviation: DeviationItem | null;
  onUpdateStatus: (status: DeviationStatus, notes?: string) => Promise<void>;
  onOpenSideBySide?: () => void;
}

export const DetailPanel: React.FC<DetailPanelProps> = ({
  deviation,
  onUpdateStatus,
  onOpenSideBySide,
}) => {
  const [commentText, setCommentText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showCommentBox, setShowCommentBox] = useState(false);

  if (!deviation) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center text-slate-400 bg-slate-50 dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800">
        <FileSearch className="w-12 h-12 mb-3 text-slate-300 dark:text-slate-600" />
        <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300">
          No Deviation Selected
        </h4>
        <p className="text-xs text-slate-500 max-w-xs mt-1">
          Click on any highlighted marker on the PDF drawing or select a deviation from the table to inspect evidence.
        </p>
      </div>
    );
  }

  const handleAction = async (status: DeviationStatus) => {
    setIsSubmitting(true);
    try {
      await onUpdateStatus(status, commentText ? commentText : undefined);
      setShowCommentBox(false);
      setCommentText('');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getSeverityBadge = (sev: SeverityLevel) => {
    switch (sev) {
      case 'CRITICAL':
        return 'bg-red-100 text-red-700 border-red-300 dark:bg-red-950 dark:text-red-300 dark:border-red-800';
      case 'HIGH':
        return 'bg-amber-100 text-amber-700 border-amber-300 dark:bg-amber-950 dark:text-amber-300 dark:border-amber-800';
      case 'MEDIUM':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300 dark:bg-yellow-950 dark:text-yellow-300 dark:border-yellow-800';
      case 'LOW':
        return 'bg-blue-100 text-blue-700 border-blue-300 dark:bg-blue-950 dark:text-blue-300 dark:border-blue-800';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-300 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700';
    }
  };

  return (
    <div className="h-full flex flex-col bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 overflow-y-auto">
      {/* Header Bar */}
      <div className="p-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-900/70 sticky top-0 z-10">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-base font-bold text-slate-900 dark:text-white">
              {deviation.deviation_number}
            </span>
            <span
              className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase tracking-wider ${getSeverityBadge(
                deviation.severity
              )}`}
            >
              {deviation.severity}
            </span>
          </div>
          <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
            Page {deviation.page_number}
          </span>
        </div>
        <div className="text-xs font-medium text-slate-500 dark:text-slate-400 mt-1 flex items-center gap-1.5">
          <span>Type:</span>
          <strong className="text-slate-800 dark:text-slate-200 font-semibold">
            {deviation.type.replace(/_/g, ' ')}
          </strong>
        </div>
      </div>

      {/* Content Body */}
      <div className="p-4 space-y-4 flex-1">
        {/* Comparison Box */}
        <div className="rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden bg-slate-50 dark:bg-slate-800/50">
          <div className="p-3 border-b border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">
              Engineering Drawing (PDF Expected)
            </div>
            <div className="text-sm font-semibold text-slate-900 dark:text-white">
              {deviation.pdf_expected}
            </div>
            {deviation.pdf_evidence.coordinates && (
              <div className="text-[11px] text-slate-500 mt-1">
                BBox: ({Math.round(deviation.pdf_evidence.coordinates.x0)},{' '}
                {Math.round(deviation.pdf_evidence.coordinates.y0)}) - (
                {Math.round(deviation.pdf_evidence.coordinates.x1)},{' '}
                {Math.round(deviation.pdf_evidence.coordinates.y1)})
              </div>
            )}
          </div>

          <div className="p-3 bg-slate-100 dark:bg-slate-900">
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">
              Configuration Export (Actual DCS/PLC)
            </div>
            <div className="text-sm font-mono font-medium text-amber-600 dark:text-amber-400">
              {deviation.config_actual}
            </div>
            <div className="text-[11px] text-slate-500 mt-1 flex items-center justify-between">
              <span>
                Block: <strong className="text-slate-700 dark:text-slate-300">{deviation.block_name || 'GENERAL'}</strong>
              </span>
              <span>
                Lines: {deviation.config_evidence.line_start} - {deviation.config_evidence.line_end}
              </span>
            </div>
          </div>
        </div>

        {/* High-Resolution Cropped Snippet */}
        {deviation.pdf_evidence.snippet_url && (
          <div className="rounded-lg border border-slate-200 dark:border-slate-700 p-3 bg-white dark:bg-slate-800">
            <div className="text-[11px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2 flex items-center justify-between">
              <span>PDF Visual Evidence Snippet</span>
              <span className="text-[10px] text-cyan-600 dark:text-cyan-400 font-mono">180 DPI Crop</span>
            </div>
            <div className="rounded border border-slate-200 dark:border-slate-700 overflow-hidden bg-slate-100 dark:bg-slate-900 flex items-center justify-center p-2">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={`http://127.0.0.1:8000${deviation.pdf_evidence.snippet_url}`}
                alt="PDF Deviation Snippet"
                className="max-h-36 object-contain rounded"
              />
            </div>
          </div>
        )}

        {/* Explanation */}
        <div className="rounded-lg border border-slate-200 dark:border-slate-700 p-3 bg-white dark:bg-slate-800">
          <div className="flex items-center space-x-1.5 text-xs font-bold text-slate-700 dark:text-slate-200 mb-1.5">
            <Sparkles className="w-3.5 h-3.5 text-cyan-600 dark:text-cyan-400" />
            <span>Engineering Explanation</span>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
            {deviation.explanation}
          </p>
        </div>

        {/* Recommended Action */}
        <div className="rounded-lg border border-cyan-200 dark:border-cyan-900/60 p-3 bg-cyan-50/50 dark:bg-cyan-950/30">
          <div className="text-xs font-bold text-cyan-800 dark:text-cyan-300 mb-1">
            Recommended Action
          </div>
          <p className="text-xs text-cyan-900 dark:text-cyan-200 leading-relaxed font-medium">
            {deviation.recommended_action}
          </p>
        </div>

        {/* Confidence Gauge */}
        <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
          <div className="flex items-center justify-between text-xs mb-1.5">
            <span className="font-semibold text-slate-600 dark:text-slate-300">
              Confidence Score
            </span>
            <span className="font-bold text-cyan-600 dark:text-cyan-400 font-mono">
              {deviation.confidence}% ({deviation.confidence_level})
            </span>
          </div>
          <div className="w-full h-2 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${
                deviation.confidence >= 90
                  ? 'bg-emerald-500'
                  : deviation.confidence >= 70
                  ? 'bg-amber-500'
                  : 'bg-red-500'
              }`}
              style={{ width: `${deviation.confidence}%` }}
            />
          </div>
        </div>

        {/* Review Notes / Audit Status */}
        {deviation.reviewer_notes && (
          <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/80">
            <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1">
              Engineer Audit Notes
            </div>
            <p className="text-xs text-slate-700 dark:text-slate-300 italic">
              &ldquo;{deviation.reviewer_notes}&rdquo;
            </p>
            {deviation.reviewed_by && (
              <div className="text-[10px] text-slate-400 mt-1">
                Reviewed by {deviation.reviewed_by} at{' '}
                {deviation.reviewed_at ? new Date(deviation.reviewed_at).toLocaleDateString() : ''}
              </div>
            )}
          </div>
        )}

        {/* Comment Box */}
        {showCommentBox && (
          <div className="space-y-2 p-3 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800">
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
              Add Engineer Note:
            </label>
            <textarea
              rows={2}
              value={commentText}
              onChange={(e) => setCommentText(e.target.value)}
              placeholder="e.g. Signal confirmed intentionally unused in Rev-04..."
              className="w-full text-xs p-2 rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
            />
          </div>
        )}
      </div>

      {/* Human-in-the-Loop Action Footer */}
      <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 sticky bottom-0">
        <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2">
          Review Decision ({deviation.status})
        </div>
        <div className="grid grid-cols-3 gap-2">
          <button
            disabled={isSubmitting}
            onClick={() => handleAction('CONFIRMED')}
            className={`flex items-center justify-center space-x-1 py-1.5 px-2 rounded text-xs font-semibold transition-all ${
              deviation.status === 'CONFIRMED'
                ? 'bg-emerald-600 text-white'
                : 'bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-950/40'
            }`}
          >
            <CheckCircle className="w-3.5 h-3.5" />
            <span>Confirm</span>
          </button>

          <button
            disabled={isSubmitting}
            onClick={() => handleAction('REJECTED')}
            className={`flex items-center justify-center space-x-1 py-1.5 px-2 rounded text-xs font-semibold transition-all ${
              deviation.status === 'REJECTED'
                ? 'bg-red-600 text-white'
                : 'bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/40'
            }`}
          >
            <XCircle className="w-3.5 h-3.5" />
            <span>Reject</span>
          </button>

          <button
            disabled={isSubmitting}
            onClick={() => setShowCommentBox(!showCommentBox)}
            className="flex items-center justify-center space-x-1 py-1.5 px-2 rounded text-xs font-semibold bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 transition-all"
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span>Comment</span>
          </button>
        </div>
      </div>
    </div>
  );
};
