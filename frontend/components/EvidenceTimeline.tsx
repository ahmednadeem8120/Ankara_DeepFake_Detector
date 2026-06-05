"use client";

import { motion } from "framer-motion";
import { AlertTriangle, AlertCircle, Info, Clock } from "lucide-react";
import type { EvidenceMarker } from "@/lib/api";

interface Props {
  evidence: EvidenceMarker[];
}

const SEVERITY_CONFIG = {
  critical: {
    color: "text-red-400",
    bg: "bg-red-500/10",
    border: "border-red-500/30",
    dot: "bg-red-500",
    Icon: AlertTriangle,
  },
  warning: {
    color: "text-amber-400",
    bg: "bg-amber-500/10",
    border: "border-amber-500/30",
    dot: "bg-amber-500",
    Icon: AlertCircle,
  },
  info: {
    color: "text-blue-400",
    bg: "bg-blue-500/10",
    border: "border-blue-500/30",
    dot: "bg-blue-400",
    Icon: Info,
  },
};

function getArtifactSeverity(type: string): "critical" | "warning" | "info" {
  if (type === "texture_anomaly") return "critical";
  return "info";
}

function formatTime(sec: number): string {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export default function EvidenceTimeline({ evidence }: Props) {
  if (!evidence.length) {
    return (
      <div className="text-center py-12 text-zinc-500">
        <Info className="w-8 h-8 mx-auto mb-3 opacity-50" />
        <p>No spatial artifacts detected</p>
        <p className="text-xs text-zinc-600 mt-1">
          The DINOv2 probe found no texture inconsistencies above threshold.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between text-sm px-1">
        <span className="text-zinc-300 font-medium">Spatial evidence</span>
        <span className="text-zinc-500">{evidence.length} markers</span>
      </div>

      {/* Evidence list */}
      <div className="relative pl-6">
        {/* Vertical timeline line */}
        <div className="absolute left-[11px] top-2 bottom-2 w-px bg-zinc-800" />

        {evidence.map((marker, i) => {
          const severity = getArtifactSeverity(marker.artifact_type);
          const config = SEVERITY_CONFIG[severity];
          const Icon = config.Icon;

          return (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.06 * i }}
              className="relative mb-3 last:mb-0"
            >
              {/* Timeline dot */}
              <div
                className={`absolute -left-6 top-3 w-[9px] h-[9px] rounded-full ${config.dot} ring-2 ring-zinc-950`}
              />

              <div className={`${config.bg} border ${config.border} rounded-lg p-3`}>
                <div className="flex items-start gap-2">
                  <Icon className={`w-4 h-4 mt-0.5 shrink-0 ${config.color}`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-xs font-medium ${config.color}`}>
                        {marker.artifact_type.replace(/_/g, " ")}
                      </span>
                      {marker.timestamp_sec > 0 && (
                        <span className="text-[10px] text-zinc-500 flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {formatTime(marker.timestamp_sec)}
                        </span>
                      )}
                      <span className="text-[10px] text-zinc-600 ml-auto">
                        {Math.round(marker.confidence * 100)}%
                      </span>
                    </div>
                    <p className="text-xs text-zinc-300 leading-relaxed">
                      {marker.description}
                    </p>
                  </div>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
