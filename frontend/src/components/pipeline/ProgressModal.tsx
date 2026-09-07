'use client';

import React from 'react';
import { PipelineStage } from '@/types';
import { CheckCircle2, Loader2, Clock, AlertCircle } from 'lucide-react';

interface ProgressModalProps {
  isOpen: boolean;
  stages: PipelineStage[];
  error?: string;
  projectName?: string;
}

export const ProgressModal: React.FC<ProgressModalProps> = ({
  isOpen,
  stages,
  error,
  projectName,
}) => {
  if (!isOpen) return null;

  const getStatusIcon = (status: PipelineStage['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="w-4 h-4 text-emerald-500" />;
      case 'in_progress':
        return <Loader2 className="w-4 h-4 text-cyan-500 animate-spin" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Clock className="w-4 h-4 text-slate-400" />;
    }
  };

  const overallProgress =
    stages.length > 0
      ? Math.round(
          stages.reduce((acc, s) => acc + (s.status === 'completed' ? 100 : s.progress), 0) /
            stages.length
        )
      : 0;

  return (
    <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full p-6 shadow-2xl text-white">
        <div className="flex items-center space-x-3 mb-4">
          <div className="w-10 h-10 rounded-lg bg-cyan-600/20 border border-cyan-500/40 flex items-center justify-center">
            <Loader2 className="w-5 h-5 text-cyan-400 animate-spin" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">
              Processing Deviation Analysis
            </h3>
            <p className="text-xs text-slate-400">
              {projectName || 'Automated Control-System Verification'}
            </p>
          </div>
        </div>

        {/* Overall Progress Bar */}
        <div className="mb-6">
          <div className="flex justify-between text-xs font-semibold mb-1.5">
            <span className="text-slate-400">Overall Verification Progress</span>
            <span className="text-cyan-400 font-mono">{overallProgress}%</span>
          </div>
          <div className="w-full h-2.5 bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-cyan-500 to-emerald-500 transition-all duration-300 rounded-full"
              style={{ width: `${overallProgress}%` }}
            />
          </div>
        </div>

        {/* Stage Steps List */}
        <div className="space-y-2.5 max-h-72 overflow-y-auto pr-1">
          {stages.map((stage, idx) => (
            <div
              key={idx}
              className={`p-2.5 rounded-lg border text-xs flex items-center justify-between transition-colors ${
                stage.status === 'in_progress'
                  ? 'bg-cyan-950/30 border-cyan-800/80'
                  : stage.status === 'completed'
                  ? 'bg-slate-800/40 border-slate-700/60'
                  : 'bg-slate-900/40 border-slate-800 opacity-60'
              }`}
            >
              <div className="flex items-center space-x-2.5">
                {getStatusIcon(stage.status)}
                <div>
                  <div
                    className={`font-medium ${
                      stage.status === 'in_progress'
                        ? 'text-cyan-300 font-semibold'
                        : stage.status === 'completed'
                        ? 'text-slate-200'
                        : 'text-slate-400'
                    }`}
                  >
                    {stage.description}
                  </div>
                  {stage.details && (
                    <div className="text-[10px] text-slate-400 mt-0.5 font-mono">
                      {stage.details}
                    </div>
                  )}
                </div>
              </div>

              {stage.status === 'in_progress' && (
                <span className="text-[11px] font-mono text-cyan-400 font-semibold">
                  {stage.progress}%
                </span>
              )}
            </div>
          ))}
        </div>

        {error && (
          <div className="mt-4 p-3 rounded-lg bg-red-950/50 border border-red-800 text-xs text-red-200">
            <strong>Analysis Failed:</strong> {error}
          </div>
        )}
      </div>
    </div>
  );
};
