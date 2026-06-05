"use client";

import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, X, FileVideo, FileImage, Scan, Clock, BookOpen, Shield } from "lucide-react";
import { analyzeStream, type AnalysisResult, type StreamEvent } from "@/lib/api";
import TrustScoreDashboard from "@/components/TrustScoreDashboard";
import EvidenceTimeline from "@/components/EvidenceTimeline";
import AnalysisProgress from "@/components/AnalysisProgress";
import ForensicExplainer from "@/components/ForensicExplainer";

type AppState = "idle" | "analyzing" | "results";
type Tab = "dashboard" | "timeline" | "explanation";

export default function Home() {
  const [appState, setAppState] = useState<AppState>("idle");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("dashboard");
  const [error, setError] = useState<string | null>(null);

  const [currentStep, setCurrentStep] = useState("");
  const [progress, setProgress] = useState(0);
  const [completedModules, setCompletedModules] = useState<Record<string, number>>({});

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const f = acceptedFiles[0];
    if (!f) return;

    setFile(f);
    setError(null);
    setResult(null);

    if (f.type.startsWith("image/")) {
      const url = URL.createObjectURL(f);
      setPreview(url);
    } else if (f.type.startsWith("video/")) {
      const url = URL.createObjectURL(f);
      setPreview(url);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "image/*": [".jpg", ".jpeg", ".png", ".webp", ".bmp"],
      "video/*": [".mp4", ".avi", ".mov", ".mkv", ".webm"],
    },
    maxSize: 500 * 1024 * 1024,
    multiple: false,
  });

  const startAnalysis = () => {
    if (!file) return;

    setAppState("analyzing");
    setCurrentStep("preprocessing");
    setProgress(0);
    setCompletedModules({});
    setError(null);

    analyzeStream(file, (event: StreamEvent) => {
      switch (event.type) {
        case "progress":
          setCurrentStep(event.data.step);
          setProgress(event.data.progress);
          break;

        case "module_complete":
          setCompletedModules((prev) => ({
            ...prev,
            [event.data.module]: event.data.deepfake_probability,
          }));
          break;

        case "result":
          setResult(event.data as AnalysisResult);
          setAppState("results");
          break;

        case "error":
          setError(event.data.message);
          setAppState("idle");
          break;
      }
    });
  };

  const reset = () => {
    setAppState("idle");
    setFile(null);
    setPreview(null);
    setResult(null);
    setError(null);
    setProgress(0);
    setCompletedModules({});
    setActiveTab("dashboard");
  };

  const TABS: { key: Tab; label: string; icon: typeof Shield }[] = [
    { key: "dashboard", label: "Trust Score", icon: Shield },
    { key: "timeline", label: "Evidence", icon: Clock },
    { key: "explanation", label: "Analysis", icon: BookOpen },
  ];

  return (
    <main className="min-h-screen bg-zinc-950 text-zinc-100">
      <header className="border-b border-zinc-800/50 px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-cyan-500 to-emerald-500 rounded-lg flex items-center justify-center">
              <Scan className="w-4 h-4 text-zinc-950" />
            </div>
            <div>
              <h1 className="text-lg font-semibold tracking-tight">ANKARA</h1>
              <p className="text-[10px] uppercase tracking-[0.2em] text-zinc-500">
                AI Multimedia Authenticity Intelligence
              </p>
            </div>
          </div>

          {appState !== "idle" && (
            <button
              onClick={reset}
              className="text-xs text-zinc-500 hover:text-zinc-300 transition-colors flex items-center gap-1"
            >
              <X className="w-3 h-3" /> New analysis
            </button>
          )}
        </div>
      </header>

      <div className="max-w-5xl mx-auto px-6 py-8">
        <AnimatePresence mode="wait">
          {appState === "idle" && (
            <motion.div
              key="idle"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="max-w-2xl mx-auto"
            >
              <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all ${
                  isDragActive
                    ? "border-cyan-500 bg-cyan-500/5"
                    : "border-zinc-700 hover:border-zinc-500 bg-zinc-900/30"
                }`}
              >
                <input {...getInputProps()} />
                <Upload className="w-10 h-10 mx-auto mb-4 text-zinc-500" />
                <p className="text-sm text-zinc-300 mb-1">
                  Drop an image or video here
                </p>
                <p className="text-xs text-zinc-600">
                  Supports JPG, PNG, WEBP, MP4, AVI, MOV — up to 500MB
                </p>
              </div>
              {file && (
                <motion.div
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-6 space-y-4"
                >
                  <div className="flex items-center gap-3 bg-zinc-900/50 border border-zinc-800 rounded-xl p-4">
                    {file.type.startsWith("image/") ? (
                      <FileImage className="w-5 h-5 text-cyan-400" />
                    ) : (
                      <FileVideo className="w-5 h-5 text-emerald-400" />
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm truncate">{file.name}</p>
                      <p className="text-xs text-zinc-500">
                        {(file.size / 1024 / 1024).toFixed(1)} MB
                      </p>
                    </div>
                    <button onClick={reset} className="text-zinc-500 hover:text-zinc-300">
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                  {preview && file.type.startsWith("image/") && (
                    <div className="rounded-xl overflow-hidden border border-zinc-800 max-h-64">
                      <img
                        src={preview}
                        alt="Preview"
                        className="w-full h-full object-contain bg-zinc-900"
                      />
                    </div>
                  )}

                  <button
                    onClick={startAnalysis}
                    className="w-full bg-gradient-to-r from-cyan-600 to-emerald-600 hover:from-cyan-500 hover:to-emerald-500 text-white font-medium py-3 rounded-xl transition-all flex items-center justify-center gap-2"
                  >
                    <Scan className="w-4 h-4" />
                    Run Forensic Analysis
                  </button>
                </motion.div>
              )}

              {error && (
                <div className="mt-4 text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg p-3">
                  {error}
                </div>
              )}
            </motion.div>
          )}

          {appState === "analyzing" && (
            <motion.div
              key="analyzing"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="max-w-lg mx-auto"
            >
              <div className="text-center mb-8">
                <Scan className="w-10 h-10 mx-auto mb-3 text-cyan-400 animate-pulse" />
                <h2 className="text-lg font-medium">Analyzing media</h2>
                <p className="text-sm text-zinc-500 mt-1">{file?.name}</p>
              </div>

              <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
                <AnalysisProgress
                  currentStep={currentStep}
                  progress={progress}
                  completedModules={completedModules}
                />
              </div>
            </motion.div>
          )}
          {appState === "results" && result && (
            <motion.div
              key="results"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <div className="flex items-center gap-1 mb-6 bg-zinc-900/50 border border-zinc-800 rounded-xl p-1 max-w-md mx-auto">
                {TABS.map((tab) => (
                  <button
                    key={tab.key}
                    onClick={() => setActiveTab(tab.key)}
                    className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-medium transition-all ${
                      activeTab === tab.key
                        ? "bg-zinc-800 text-zinc-100"
                        : "text-zinc-500 hover:text-zinc-300"
                    }`}
                  >
                    <tab.icon className="w-3.5 h-3.5" />
                    {tab.label}
                  </button>
                ))}
              </div>

              <div className="max-w-2xl mx-auto">
                <AnimatePresence mode="wait">
                  {activeTab === "dashboard" && (
                    <motion.div key="dashboard" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                      <TrustScoreDashboard result={result} />
                    </motion.div>
                  )}

                  {activeTab === "timeline" && (
                    <motion.div key="timeline" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                      <EvidenceTimeline evidence={result.evidence} />
                    </motion.div>
                  )}

                  {activeTab === "explanation" && (
                    <motion.div key="explanation" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                      <ForensicExplainer explanation={result.explanation} />
                    </motion.div>
                  )}
                </AnimatePresence>
                <div className="mt-8 text-center text-[10px] text-zinc-600 space-x-4">
                  <span>Request: {result.request_id}</span>
                  <span>Processed in {result.processing_time_sec}s</span>
                  <span>Device: MPS (Apple Silicon)</span>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </main>
  );
}
