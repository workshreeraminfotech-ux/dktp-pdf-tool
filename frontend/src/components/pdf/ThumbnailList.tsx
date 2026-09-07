'use client';

import React from 'react';
import { FileText, AlertCircle } from 'lucide-react';

interface ThumbnailListProps {
  pageCount: number;
  currentPage: number;
  pageDeviationCounts: Record<number, number>;
  onSelectPage: (page: number) => void;
}

export const ThumbnailList: React.FC<ThumbnailListProps> = ({
  pageCount,
  currentPage,
  pageDeviationCounts,
  onSelectPage,
}) => {
  return (
    <div className="w-48 bg-slate-50 dark:bg-slate-900/90 border-r border-slate-200 dark:border-slate-800 flex flex-col h-full">
      <div className="p-3 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
        <span className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
          Pages ({pageCount})
        </span>
        <span className="text-[10px] text-slate-400">Deviations</span>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {Array.from({ length: pageCount }, (_, i) => i + 1).map((pageNum) => {
          const devCount = pageDeviationCounts[pageNum] || 0;
          const isSelected = currentPage === pageNum;

          return (
            <button
              key={pageNum}
              onClick={() => onSelectPage(pageNum)}
              className={`w-full text-left p-2 rounded-lg border transition-all flex flex-col items-center ${
                isSelected
                  ? 'border-cyan-500 bg-cyan-50/60 dark:bg-cyan-950/40 shadow-sm ring-1 ring-cyan-500'
                  : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-800/60 hover:border-slate-400'
              }`}
            >
              {/* Thumbnail Representation */}
              <div className="w-full aspect-[4/3] bg-slate-100 dark:bg-slate-900 rounded border border-slate-200 dark:border-slate-700 flex flex-col items-center justify-center relative overflow-hidden group">
                <FileText className="w-6 h-6 text-slate-300 dark:text-slate-600 group-hover:scale-110 transition-transform" />
                <span className="text-[10px] font-semibold text-slate-500 mt-1">
                  Page {pageNum}
                </span>

                {devCount > 0 && (
                  <div className="absolute top-1 right-1 bg-amber-500 text-white text-[9px] font-bold px-1.5 py-0.5 rounded-full shadow-sm flex items-center space-x-0.5">
                    <span>{devCount}</span>
                  </div>
                )}
              </div>

              <div className="w-full flex items-center justify-between mt-1 px-1">
                <span className="text-[11px] font-medium text-slate-600 dark:text-slate-400">
                  Drawing {pageNum}
                </span>
                {devCount > 0 ? (
                  <span className="text-[10px] font-bold text-amber-600 dark:text-amber-400 flex items-center gap-0.5">
                    <AlertCircle className="w-3 h-3" />
                    {devCount}
                  </span>
                ) : (
                  <span className="text-[10px] text-slate-400">Clear</span>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
