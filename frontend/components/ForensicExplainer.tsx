"use client";

import { motion } from "framer-motion";
import { BookOpen } from "lucide-react";

interface Props {
  explanation: string | null;
}

export default function ForensicExplainer({ explanation }: Props) {
  if (!explanation) return null;

  const sections = explanation.split("\n").reduce<{ title: string; content: string[] }[]>(
    (acc, line) => {
      const trimmed = line.trim();
      if (!trimmed) return acc;
      if (
        trimmed.startsWith("SUMMARY:") ||
        trimmed.startsWith("KEY FINDINGS:") ||
        trimmed.startsWith("TECHNICAL ANALYSIS:") ||
        trimmed.startsWith("CITED RESEARCH:") ||
        trimmed.startsWith("CONFIDENCE ASSESSMENT:")
      ) {
        const [title, ...rest] = trimmed.split(":");
        const content = rest.join(":").trim();
        acc.push({ title: title.trim(), content: content ? [content] : [] });
      } else if (acc.length > 0) {
        acc[acc.length - 1].content.push(trimmed);
      } else {
        acc.push({ title: "Analysis", content: [trimmed] });
      }
      return acc;
    },
    []
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
      className="space-y-4"
    >
      <div className="flex items-center gap-2 text-sm text-zinc-400">
        <BookOpen className="w-4 h-4" />
        <span className="uppercase tracking-wider text-xs font-medium">
          Ankara Forensic Reasoning Engine
        </span>
      </div>

      <div className="space-y-3">
        {sections.map((section, i) => (
          <div key={i} className="bg-zinc-900/40 border border-zinc-800 rounded-lg p-4">
            <h4 className="text-xs font-medium text-zinc-400 uppercase tracking-wider mb-2">
              {section.title}
            </h4>
            <div className="text-sm text-zinc-300 leading-relaxed space-y-1">
              {section.content.map((line, j) => (
                <p
                  key={j}
                  className={
                    line.startsWith("  -") || line.startsWith("- ")
                      ? "pl-3 border-l border-zinc-700"
                      : ""
                  }
                >
                  {line.replace(/^  - /, "").replace(/^- /, "")}
                </p>
              ))}
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
