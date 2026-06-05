const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface EvidenceMarker {
  timestamp_sec: number;
  frame_index: number;
  artifact_type: string;
  description: string;
  confidence: number;
}

export interface AnalysisResult {
  request_id: string;
  media_type: string;
  authenticity_score: number;
  deepfake_probability: number;
  confidence_level: "high" | "medium" | "low";
  evidence: EvidenceMarker[];
  explanation: string | null;
  metadata?: {
    dino_score?: number;
    frames_analyzed?: number;
    per_frame_scores?: number[];
  };
  processing_time_sec?: number;
}

export interface StreamEvent {
  type: "progress" | "module_complete" | "result" | "error";
  data: any;
}

export async function analyzeMedia(file: File): Promise<AnalysisResult> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/api/analyze`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Analysis failed");
  }

  return response.json();
}

export async function quickAnalyze(file: File): Promise<{
  request_id: string;
  deepfake_probability: number;
  confidence: number;
  evidence_count: number;
  processing_time_sec: number;
}> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/api/analyze/quick`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) throw new Error("Quick analysis failed");
  return response.json();
}

export function analyzeStream(
  file: File,
  onEvent: (event: StreamEvent) => void
): () => void {
  const formData = new FormData();
  formData.append("file", file);

  const controller = new AbortController();

  (async () => {
    try {
      const response = await fetch(`${API_BASE}/api/analyze/stream`, {
        method: "POST",
        body: formData,
        signal: controller.signal,
      });

      if (!response.ok) {
        onEvent({ type: "error", data: { message: "Stream failed" } });
        return;
      }

      const reader = response.body?.getReader();
      if (!reader) return;

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        let currentEvent = "";
        for (const line of lines) {
          if (line.startsWith("event: ")) {
            currentEvent = line.slice(7);
          } else if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              onEvent({ type: currentEvent as StreamEvent["type"], data });
            } catch {}
          }
        }
      }
    } catch (err: any) {
      if (err.name !== "AbortError") {
        onEvent({ type: "error", data: { message: err.message } });
      }
    }
  })();

  return () => controller.abort();
}

export async function searchKnowledge(
  query: string,
  n: number = 5
): Promise<{ query: string; results: any[] }> {
  const response = await fetch(
    `${API_BASE}/api/rag/search?q=${encodeURIComponent(query)}&n=${n}`
  );
  if (!response.ok) throw new Error("Search failed");
  return response.json();
}

export async function ingestPaper(file: File): Promise<any> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/api/rag/ingest`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) throw new Error("Ingestion failed");
  return response.json();
}
