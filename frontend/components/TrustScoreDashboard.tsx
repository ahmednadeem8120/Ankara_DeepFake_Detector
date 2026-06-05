"use client";

import { motion } from "framer-motion";
import { ShieldAlert, ShieldCheck, ShieldQuestion } from "lucide-react";
import { AnalysisResult } from "@/lib/api";

interface Props {
  result: AnalysisResult;
}

function getScoreColor(score: number): string {
  if (score >= 70) return "text-emerald-500";
  if (score >= 40) return "text-amber-500";
  return "text-red-500";
}

function getConfidenceBadge(level: string) {
  const styles: Record<string, string> = {
    high: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    medium: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    low: "bg-zinc-500/10 text-zinc-400 border-zinc-500/20",
  };
  return styles[level] || styles.low;
}

export default function TrustScoreDashboard({ result }: Props) {
  const score = Math.round(result.authenticity_score);
  const fakePercent = Math.round(result.deepfake_probability * 100);
  const verdict =
    score >= 70 ? "Likely Authentic" : score >= 40 ? "Inconclusive" : "Likely Manipulated";
  const frames = result.metadata?.frames_analyzed;

  return (
    <div className="space-y-6">
      {/* Main score */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="text-center py-8"
      >
        <div className="inline-flex items-center gap-3 mb-2">
          {score >= 70 ? (
            <ShieldCheck className="w-8 h-8 text-emerald-500" />
          ) : score >= 40 ? (
            <ShieldQuestion className="w-8 h-8 text-amber-500" />
          ) : (
            <ShieldAlert className="w-8 h-8 text-red-500" />
          )}
          <span className="text-sm uppercase tracking-wider text-zinc-400">
            Authenticity Score
          </span>
        </div>

        <div className={`text-7xl font-bold tabular-nums ${getScoreColor(score)}`}>
          {score}
          <span className="text-2xl text-zinc-500">%</span>
        </div>

        <div className="mt-2 text-sm text-zinc-400">{verdict}</div>

        <div className="mt-3 flex items-center justify-center gap-2">
          <span
            className={`text-xs font-medium px-3 py-1 rounded-full border ${getConfidenceBadge(
              result.confidence_level
            )}`}
          >
            {result.confidence_level.toUpperCase()} CONFIDENCE
          </span>
        </div>
      </motion.div>

      {/* Spatial detector card */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-5"
      >
        <div className="flex items-center gap-2 mb-3">
          <span className="text-lg">🔬</span>
          <span className="text-xs text-zinc-400 uppercase tracking-wider">
            Spatial Analysis — DINOv2
          </span>
        </div>

        <div className="flex items-end justify-between">
          <div>
            <span className="text-[11px] text-zinc-500 uppercase tracking-wider">
              Deepfake probability
            </span>
            <div
              className={`text-3xl font-bold tabular-nums ${
                fakePercent > 60 ? "text-red-400" : fakePercent > 40 ? "text-amber-400" : "text-emerald-400"
              }`}
            >
              {fakePercent}%
            </div>
          </div>
          {frames !== undefined && (
            <span className="text-xs text-zinc-500">{frames} frames analyzed</span>
          )}
        </div>

        {/* Probability bar */}
        <div className="mt-3 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${fakePercent}%` }}
            transition={{ delay: 0.2, duration: 0.8, ease: "easeOut" }}
            className={`h-full rounded-full ${
              fakePercent > 60 ? "bg-red-500" : fakePercent > 40 ? "bg-amber-500" : "bg-emerald-500"
            }`}
          />
        </div>

        <p className="mt-3 text-xs text-zinc-500 leading-relaxed">
          A linear probe on frozen DINOv2 self-supervised features detects spatial
          texture and structural artifacts left by face-generation models.
        </p>
      </motion.div>
    </div>
  );
}
