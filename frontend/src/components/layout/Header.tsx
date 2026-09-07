'use client';

import React from 'react';
import Link from 'next/link';
import { Layers, Activity, Share2, PlusCircle } from 'lucide-react';

interface HeaderProps {
  projectName?: string;
  pdfRevision?: string;
  configRevision?: string;
  onNewAnalysis?: () => void;
  onShare?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  projectName = "Deviation Intelligence",
  pdfRevision,
  configRevision,
  onNewAnalysis,
  onShare,
}) => {
  return (
    <header className="h-16 bg-white border-b border-slate-200 text-slate-800 flex items-center justify-between px-6 z-30 sticky top-0 shadow-xs">
      {/* Brand & Project Info */}
      <div className="flex items-center space-x-4">
        <Link href="/" className="flex items-center space-x-3 group">
          <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center shadow-md shadow-blue-600/20 group-hover:bg-blue-700 transition-colors">
            <Layers className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="font-bold text-sm tracking-tight text-slate-900 flex items-center gap-2">
              DKTP Logic Audit
              <span className="text-[10px] uppercase font-bold bg-blue-50 text-blue-700 border border-blue-200 px-1.5 py-0.5 rounded">
                DCS / PLC
              </span>
            </div>
            <div className="text-xs text-slate-500 truncate max-w-[260px] font-medium">
              {projectName}
            </div>
          </div>
        </Link>

        {(pdfRevision || configRevision) && (
          <div className="hidden md:flex items-center space-x-2 pl-4 border-l border-slate-200 text-xs text-slate-600">
            {pdfRevision && (
              <span className="bg-slate-100 px-2.5 py-0.5 rounded border border-slate-200">
                PDF: <strong className="text-blue-700">{pdfRevision}</strong>
              </span>
            )}
            {configRevision && (
              <span className="bg-slate-100 px-2.5 py-0.5 rounded border border-slate-200">
                CFG: <strong className="text-emerald-700">{configRevision}</strong>
              </span>
            )}
          </div>
        )}
      </div>

      {/* Navigation & Action CTAs */}
      <div className="flex items-center space-x-3">
        {onShare && (
          <button
            onClick={onShare}
            className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg border border-slate-200 transition"
          >
            <Share2 className="w-3.5 h-3.5 text-slate-600" />
            <span>Share Audit</span>
          </button>
        )}

        <Link
          href="/"
          className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 transition"
        >
          <Activity className="w-3.5 h-3.5" />
          <span>Dashboard</span>
        </Link>

        {onNewAnalysis && (
          <button
            onClick={onNewAnalysis}
            className="flex items-center space-x-1.5 px-3.5 py-1.5 text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition"
          >
            <PlusCircle className="w-3.5 h-3.5" />
            <span>New Analysis</span>
          </button>
        )}
      </div>
    </header>
  );
};
