'use client';

import React from 'react';
import { AnalysisStats, SeverityLevel } from '@/types';
import { AlertOctagon, AlertTriangle, AlertCircle, Info, HelpCircle, Layers } from 'lucide-react';

interface MetricsCardsProps {
  stats: AnalysisStats;
  selectedSeverity: SeverityLevel | 'ALL' | 'REVIEW';
  onSelectSeverity: (sev: SeverityLevel | 'ALL' | 'REVIEW') => void;
}

export const MetricsCards: React.FC<MetricsCardsProps> = ({
  stats,
  selectedSeverity,
  onSelectSeverity,
}) => {
  const cards = [
    {
      id: 'ALL' as const,
      label: 'Total Deviations',
      count: stats.total_deviations,
      icon: Layers,
      color: 'text-slate-900',
      bg: 'bg-white',
      border: 'border-slate-200',
      activeBorder: 'ring-2 ring-blue-600 border-blue-600',
    },
    {
      id: 'CRITICAL' as const,
      label: 'Critical Risk',
      count: stats.critical_count,
      icon: AlertOctagon,
      color: 'text-red-600',
      bg: 'bg-white',
      border: 'border-slate-200',
      activeBorder: 'ring-2 ring-red-600 border-red-600',
    },
    {
      id: 'HIGH' as const,
      label: 'High Severity',
      count: stats.high_count,
      icon: AlertTriangle,
      color: 'text-amber-600',
      bg: 'bg-white',
      border: 'border-slate-200',
      activeBorder: 'ring-2 ring-amber-600 border-amber-600',
    },
    {
      id: 'MEDIUM' as const,
      label: 'Medium Severity',
      count: stats.medium_count,
      icon: AlertCircle,
      color: 'text-yellow-600',
      bg: 'bg-white',
      border: 'border-slate-200',
      activeBorder: 'ring-2 ring-yellow-600 border-yellow-600',
    },
    {
      id: 'LOW' as const,
      label: 'Low Severity',
      count: stats.low_count,
      icon: Info,
      color: 'text-blue-600',
      bg: 'bg-white',
      border: 'border-slate-200',
      activeBorder: 'ring-2 ring-blue-600 border-blue-600',
    },
    {
      id: 'REVIEW' as const,
      label: 'Review Required',
      count: stats.review_required_count,
      icon: HelpCircle,
      color: 'text-purple-600',
      bg: 'bg-white',
      border: 'border-slate-200',
      activeBorder: 'ring-2 ring-purple-600 border-purple-600',
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-3">
      {cards.map((c) => {
        const Icon = c.icon;
        const isSelected = selectedSeverity === c.id;
        return (
          <button
            key={c.id}
            onClick={() => onSelectSeverity(c.id)}
            className={`flex flex-col p-3 rounded-xl border text-left transition-all ${c.bg} ${c.border} ${
              isSelected ? `${c.activeBorder} shadow-sm bg-blue-50/20` : 'hover:border-slate-300 hover:shadow-xs'
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                {c.label}
              </span>
              <Icon className={`w-4 h-4 ${c.color}`} />
            </div>
            <div className={`text-2xl font-black tracking-tight ${c.color}`}>
              {c.count}
            </div>
          </button>
        );
      })}
    </div>
  );
};
