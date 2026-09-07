'use client';

import React, { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { uploadAnalysis } from '@/lib/api';
import {
  FileText,
  FileCode,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Layers,
  FileSpreadsheet,
  X,
  Upload,
  Cpu,
  ShieldAlert
} from 'lucide-react';

export default function CleanHomePage() {
  const router = useRouter();
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [txtFile, setTxtFile] = useState<File | null>(null);
  const [projectName, setProjectName] = useState('TPP Logic Audit');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const pdfInputRef = useRef<HTMLInputElement | null>(null);
  const txtInputRef = useRef<HTMLInputElement | null>(null);

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const handleCompare = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!pdfFile || !txtFile) {
      setError('Please select both the Drawing PDF file and the Text Configuration file.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('pdf_file', pdfFile);
      formData.append('config_file', txtFile);
      formData.append('project_name', projectName || 'TPP Logic Compare');

      const res = await uploadAnalysis(formData);
      router.push(`/analyses/${res.job_id}`);
    } catch (err: any) {
      console.error(err);
      setError(err?.response?.data?.detail || 'Failed to start comparison. Please check backend connection.');
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 flex flex-col font-sans selection:bg-blue-100 selection:text-blue-900">
      {/* Top Header */}
      <header className="border-b border-slate-200 bg-white/95 backdrop-blur sticky top-0 z-20 px-8 py-3.5 flex items-center justify-between shadow-sm">
        <div className="flex items-center space-x-3.5">
          <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center shadow-md shadow-blue-600/20 text-white font-black text-lg">
            <Layers className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-base font-bold text-slate-900 tracking-tight">
                DKTP Logic Deviation Audit
              </h1>
              <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                v2.0 Pro
              </span>
            </div>
            <p className="text-xs text-slate-500 font-medium">
              Precision Cross-Comparison for Engineering Drawings & DCS Logic
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>AI Intelligence Active</span>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-5xl w-full mx-auto p-6 md:p-10 flex flex-col items-center justify-center">
        {/* Intro Tagline */}
        <div className="text-center max-w-2xl mb-8">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-xs font-semibold mb-3 shadow-xs">
            <Sparkles className="w-3.5 h-3.5 text-blue-600" />
            <span>Automated Missing Logic & Parameter Mismatch Detection</span>
          </div>
          <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight sm:text-4xl">
            Compare Drawing PDF & Text Files
          </h2>
          <p className="mt-2 text-sm text-slate-600 leading-relaxed">
            Upload your schematic drawing PDF and DCS configuration text file. The AI engine will cross-verify logic blocks, timers, interlocks, and highlight every deviation line-by-line.
          </p>
        </div>

        {/* Upload Card */}
        <div className="w-full bg-white border border-slate-200/90 rounded-2xl p-7 md:p-9 shadow-xl shadow-slate-200/50">
          {error && (
            <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center space-x-2.5">
              <AlertCircle className="w-4 h-4 flex-shrink-0 text-red-600" />
              <span className="font-medium">{error}</span>
            </div>
          )}

          <form onSubmit={handleCompare} className="space-y-6">
            {/* Project Name Field */}
            <div>
              <label className="text-xs font-bold text-slate-700 uppercase tracking-wider block mb-2">
                Project / Plant Unit Name
              </label>
              <input
                type="text"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                placeholder="e.g. Unit-1 Boiler Feed Pump Logic"
                className="w-full text-sm px-4 py-3 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 font-medium placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition"
              />
            </div>

            {/* Dual Upload Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {/* File 1: PDF */}
              <div
                onClick={() => pdfInputRef.current?.click()}
                className={`group relative border-2 border-dashed rounded-2xl p-6 text-center transition-all cursor-pointer ${
                  pdfFile
                    ? 'border-blue-500 bg-blue-50/40 shadow-sm'
                    : 'border-slate-300 hover:border-blue-400 hover:bg-slate-50/60 bg-white'
                }`}
              >
                <input
                  ref={pdfInputRef}
                  type="file"
                  accept=".pdf"
                  onChange={(e) => setPdfFile(e.target.files?.[0] || null)}
                  className="hidden"
                />

                <div className="w-12 h-12 rounded-2xl bg-blue-100 text-blue-600 flex items-center justify-center mx-auto mb-3 group-hover:scale-105 transition">
                  <FileText className="w-6 h-6" />
                </div>

                <h3 className="text-sm font-bold text-slate-900 mb-1">
                  1. Engineering Drawing PDF
                </h3>
                <p className="text-xs text-slate-500 mb-4">
                  Multi-page schematic or logic drawings (.pdf)
                </p>

                {pdfFile ? (
                  <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-blue-100/80 border border-blue-200 text-blue-900 text-xs font-semibold max-w-full truncate">
                    <CheckCircle2 className="w-4 h-4 text-blue-600 flex-shrink-0" />
                    <span className="truncate">{pdfFile.name}</span>
                    <span className="text-[10px] text-blue-700 flex-shrink-0 font-mono">
                      ({formatFileSize(pdfFile.size)})
                    </span>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setPdfFile(null);
                      }}
                      className="p-0.5 hover:bg-blue-200 rounded text-blue-700"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ) : (
                  <div className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition">
                    <Upload className="w-3.5 h-3.5" />
                    <span>Choose PDF File</span>
                  </div>
                )}
              </div>

              {/* File 2: TXT */}
              <div
                onClick={() => txtInputRef.current?.click()}
                className={`group relative border-2 border-dashed rounded-2xl p-6 text-center transition-all cursor-pointer ${
                  txtFile
                    ? 'border-emerald-500 bg-emerald-50/40 shadow-sm'
                    : 'border-slate-300 hover:border-emerald-400 hover:bg-slate-50/60 bg-white'
                }`}
              >
                <input
                  ref={txtInputRef}
                  type="file"
                  accept=".txt,.csv,.json,.xml"
                  onChange={(e) => setTxtFile(e.target.files?.[0] || null)}
                  className="hidden"
                />

                <div className="w-12 h-12 rounded-2xl bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto mb-3 group-hover:scale-105 transition">
                  <FileCode className="w-6 h-6" />
                </div>

                <h3 className="text-sm font-bold text-slate-900 mb-1">
                  2. DCS Text Configuration
                </h3>
                <p className="text-xs text-slate-500 mb-4">
                  Master configuration or export text (.txt, .csv)
                </p>

                {txtFile ? (
                  <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-emerald-100/80 border border-emerald-200 text-emerald-900 text-xs font-semibold max-w-full truncate">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                    <span className="truncate">{txtFile.name}</span>
                    <span className="text-[10px] text-emerald-700 flex-shrink-0 font-mono">
                      ({formatFileSize(txtFile.size)})
                    </span>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setTxtFile(null);
                      }}
                      className="p-0.5 hover:bg-emerald-200 rounded text-emerald-700"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ) : (
                  <div className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition">
                    <Upload className="w-3.5 h-3.5" />
                    <span>Choose Text File</span>
                  </div>
                )}
              </div>
            </div>

            {/* AI Engine Status Banner */}
            <div className="flex items-center justify-between p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-700">
              <div className="flex items-center space-x-2.5">
                <div className="p-1 rounded-md bg-blue-100 text-blue-600">
                  <Cpu className="w-4 h-4" />
                </div>
                <div>
                  <span className="font-bold text-slate-900">AI Logic Intelligence Engine</span>
                  <span className="text-slate-500 ml-1.5 hidden sm:inline">
                    &bull; GPT-4o Vision OCR & Rule-Based Cross Check
                  </span>
                </div>
              </div>
              <span className="px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold text-[11px] border border-emerald-200">
                Ready
              </span>
            </div>

            {/* Action Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-4 rounded-xl bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-bold text-base shadow-lg shadow-blue-600/25 flex items-center justify-center space-x-2 transition disabled:opacity-60 cursor-pointer"
            >
              {isLoading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Processing & Comparing Logic Files...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5 text-blue-200" />
                  <span>Compare Files & Highlight Deviations</span>
                  <ArrowRight className="w-5 h-5 text-white" />
                </>
              )}
            </button>
          </form>

          {/* 3 Step Workflow Footer */}
          <div className="mt-8 pt-6 border-t border-slate-100 grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
              <span className="text-xs font-bold text-slate-900 block mb-0.5">1. Upload PDF + TXT</span>
              <span className="text-[11px] text-slate-500">Drawing schematic & master DCS code</span>
            </div>
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
              <span className="text-xs font-bold text-slate-900 block mb-0.5">2. Deep AI Logic Audit</span>
              <span className="text-[11px] text-slate-500">Detects missing steps & timers</span>
            </div>
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
              <span className="text-xs font-bold text-slate-900 block mb-0.5">3. Highlighted Text & Excel</span>
              <span className="text-[11px] text-slate-500">Visual red ribbons & export sheet</span>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
