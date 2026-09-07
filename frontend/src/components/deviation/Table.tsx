'use client';

import React, { useState, useMemo } from 'react';
import { DeviationItem, SeverityLevel, DeviationStatus } from '@/types';
import {
  Search,
  Download,
  Filter,
  FileSpreadsheet,
  FileText,
  CheckCircle,
  XCircle,
  HelpCircle,
  ArrowUpDown,
  ExternalLink,
} from 'lucide-react';

interface TableProps {
  deviations: DeviationItem[];
  selectedDeviation: DeviationItem | null;
  onSelectDeviation: (dev: DeviationItem) => void;
  analysisId: string;
}

export const Table: React.FC<TableProps> = ({
  deviations,
  selectedDeviation,
  onSelectDeviation,
  analysisId,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  const filteredDeviations = useMemo(() => {
    return deviations.filter((dev) => {
      const matchesSearch =
        dev.deviation_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
        dev.type.toLowerCase().includes(searchTerm.toLowerCase()) ||
        dev.pdf_expected.toLowerCase().includes(searchTerm.toLowerCase()) ||
        dev.config_actual.toLowerCase().includes(searchTerm.toLowerCase()) ||
        dev.explanation.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (dev.block_name && dev.block_name.toLowerCase().includes(searchTerm.toLowerCase()));

      const matchesStatus =
        statusFilter === 'ALL' || dev.status === statusFilter;

      return matchesSearch && matchesStatus;
    });
  }, [deviations, searchTerm, statusFilter]);

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
        return 'bg-slate-100 text-slate-700 border-slate-300 dark:bg-slate-800 dark:text-slate-300';
    }
  };

  const getStatusBadge = (status: DeviationStatus) => {
    switch (status) {
      case 'CONFIRMED':
        return 'text-emerald-600 bg-emerald-50 border-emerald-200 dark:bg-emerald-950 dark:text-emerald-400 dark:border-emerald-800';
      case 'REJECTED':
        return 'text-red-600 bg-red-50 border-red-200 dark:bg-red-950 dark:text-red-400 dark:border-red-800';
      case 'UNDER_REVIEW':
        return 'text-purple-600 bg-purple-50 border-purple-200 dark:bg-purple-950 dark:text-purple-400 dark:border-purple-800';
      default:
        return 'text-slate-600 bg-slate-50 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700';
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 flex flex-col h-72">
      {/* Controls Bar */}
      <div className="p-3 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between gap-4">
        <div className="flex items-center space-x-3 flex-1">
          {/* Search Box */}
          <div className="relative max-w-xs w-full">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search tag, block, explanation..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full text-xs pl-8 pr-3 py-1.5 rounded-md border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-cyan-500"
            />
          </div>

          {/* Status Filter */}
          <div className="flex items-center space-x-1.5 text-xs text-slate-600 dark:text-slate-300">
            <Filter className="w-3.5 h-3.5" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="text-xs py-1 px-2 rounded border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
            >
              <option value="ALL">All Statuses</option>
              <option value="OPEN">Open</option>
              <option value="CONFIRMED">Confirmed</option>
              <option value="REJECTED">Rejected</option>
              <option value="UNDER_REVIEW">Under Review</option>
            </select>
          </div>
        </div>

        {/* Export Buttons */}
        <div className="flex items-center space-x-2">
          <a
            href={`http://127.0.0.1:8000/api/files/download/${analysisId}/report-pdf`}
            download
            className="flex items-center space-x-1 px-2.5 py-1 text-xs font-semibold text-slate-700 dark:text-slate-200 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded border border-slate-300 dark:border-slate-700 transition-colors"
          >
            <FileText className="w-3.5 h-3.5 text-red-500" />
            <span>PDF Report</span>
          </a>

          <a
            href={`http://127.0.0.1:8000/api/files/download/${analysisId}/report-xlsx`}
            download
            className="flex items-center space-x-1 px-2.5 py-1 text-xs font-semibold text-slate-700 dark:text-slate-200 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded border border-slate-300 dark:border-slate-700 transition-colors"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-500" />
            <span>Excel (XLSX)</span>
          </a>

          <a
            href={`http://127.0.0.1:8000/api/files/download/${analysisId}/annotated`}
            download
            className="flex items-center space-x-1 px-2.5 py-1 text-xs font-semibold text-white bg-cyan-600 hover:bg-cyan-500 rounded transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Highlighted PDF</span>
          </a>
        </div>
      </div>

      {/* Table Data */}
      <div className="flex-1 overflow-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead className="bg-slate-50 dark:bg-slate-800/80 sticky top-0 border-b border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400 text-[11px] uppercase tracking-wider">
            <tr>
              <th className="py-2 px-3 font-bold">ID</th>
              <th className="py-2 px-3 font-bold">Severity</th>
              <th className="py-2 px-3 font-bold">Deviation Type</th>
              <th className="py-2 px-3 font-bold">Page</th>
              <th className="py-2 px-3 font-bold">Block</th>
              <th className="py-2 px-3 font-bold">PDF Drawing Value</th>
              <th className="py-2 px-3 font-bold">Configuration Value</th>
              <th className="py-2 px-3 font-bold">Confidence</th>
              <th className="py-2 px-3 font-bold">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {filteredDeviations.length === 0 ? (
              <tr>
                <td colSpan={9} className="py-8 text-center text-slate-400">
                  No deviations match your search filters.
                </td>
              </tr>
            ) : (
              filteredDeviations.map((dev) => {
                const isSelected = selectedDeviation?.id === dev.id;
                return (
                  <tr
                    key={dev.id}
                    onClick={() => onSelectDeviation(dev)}
                    className={`cursor-pointer transition-colors ${
                      isSelected
                        ? 'bg-cyan-50/80 dark:bg-cyan-950/40 font-medium'
                        : 'hover:bg-slate-50 dark:hover:bg-slate-800/50'
                    }`}
                  >
                    <td className="py-2 px-3 font-bold text-slate-900 dark:text-white">
                      {dev.deviation_number}
                    </td>
                    <td className="py-2 px-3">
                      <span
                        className={`text-[10px] font-bold px-1.5 py-0.5 rounded border uppercase ${getSeverityBadge(
                          dev.severity
                        )}`}
                      >
                        {dev.severity}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-slate-700 dark:text-slate-300">
                      {dev.type.replace(/_/g, ' ')}
                    </td>
                    <td className="py-2 px-3 text-slate-600 dark:text-slate-400">
                      Page {dev.page_number}
                    </td>
                    <td className="py-2 px-3 font-mono text-slate-600 dark:text-slate-400">
                      {dev.block_name || '-'}
                    </td>
                    <td className="py-2 px-3 font-medium text-slate-900 dark:text-white max-w-xs truncate">
                      {dev.pdf_expected}
                    </td>
                    <td className="py-2 px-3 font-mono text-amber-600 dark:text-amber-400 max-w-xs truncate">
                      {dev.config_actual}
                    </td>
                    <td className="py-2 px-3 font-bold font-mono text-cyan-600 dark:text-cyan-400">
                      {dev.confidence}%
                    </td>
                    <td className="py-2 px-3">
                      <span
                        className={`text-[10px] font-semibold px-2 py-0.5 rounded border ${getStatusBadge(
                          dev.status
                        )}`}
                      >
                        {dev.status}
                      </span>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
