"use client";

import { motion } from "framer-motion";
import { Loader2, Check } from "lucide-react";

interface Props {
  currentStep: string;
  progress: number;
  completedModules: Record<string, number>;
}

const STEPS = [
  { key: "preprocessing", label: "Preprocessing" },
  { key: "spatial_analysis", label: "Spatial analysis (DINOv2)" },
  { key: "explanation", label: "Forensic reasoning (RAG + Llama 3.2)" },
  { key: "complete", label: "Complete" },
];

export default function AnalysisProgress({ currentStep, progress, completedModules }: Props) {
  const currentIndex = STEPS.findIndex((s) => s.key === currentStep);

  return (
    <div className="space-y-3">
      <div className="h-1 bg-zinc-800 rounded-full overflow-hidden">
        <motion.div
          className="h-full bg-gradient-to-r from-cyan-500 to-emerald-500 rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.4, ease: "easeOut" }}
        />
      </div>

      <div className="text-xs text-zinc-500 text-right tabular-nums">
        {Math.round(progress)}%
      </div>

      <div className="space-y-1.5">
        {STEPS.map((step, i) => {
          const isDone = i < currentIndex;
          const isCurrent = step.key === currentStep;
          const moduleResult = completedModules[step.key.replace("_analysis", "")];

          return (
            <div
              key={step.key}
              className={`flex items-center gap-2.5 py-1 px-2 rounded text-xs transition-colors ${
                isCurrent
                  ? "text-zinc-100 bg-zinc-800/50"
                  : isDone
                  ? "text-zinc-400"
                  : "text-zinc-600"
              }`}
            >
              {isDone ? (
                <Check className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
              ) : isCurrent ? (
                <Loader2 className="w-3.5 h-3.5 text-cyan-400 animate-spin shrink-0" />
              ) : (
                <div className="w-3.5 h-3.5 rounded-full border border-zinc-700 shrink-0" />
              )}

              <span className="flex-1">{step.label}</span>

              {moduleResult !== undefined && (
                <span
                  className={`tabular-nums font-medium ${
                    moduleResult > 0.6
                      ? "text-red-400"
                      : moduleResult > 0.4
                      ? "text-amber-400"
                      : "text-emerald-400"
                  }`}
                >
                  {Math.round(moduleResult * 100)}%
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
