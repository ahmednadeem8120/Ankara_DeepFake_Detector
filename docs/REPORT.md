# Ankara — System Report & Analysis

**System:** DINOv2 spatial deepfake detector + RAG forensic reasoning (Llama 3.2, local)
**Date:** 2026-06-04

---

## 1. Overview

Ankara detects deepfakes from a single, validated signal: a **linear probe on a frozen
DINOv2-base vision transformer**. The probe reads the DINOv2 CLS feature of each frame
and outputs a deepfake probability. For video, up to 16 evenly-sampled full frames are
scored and averaged. Results are explained by a **local Llama 3.2 model (via Ollama)**
grounded in a ChromaDB research knowledge base.

The system is deliberately **single-model**: spatial detection is the component that
demonstrably works on the available data, so it is the only one shipped.

---

## 2. Model

| Property | Value |
|----------|-------|
| Backbone | `facebook/dinov2-base` (frozen, ~87M params) |
| Probe | LayerNorm(768) → Linear(768→128) → GELU → Dropout(0.2) → Linear(128→1) → Sigmoid |
| Trainable params | ~100K |
| Input | Full frame, resized 224×224, ImageNet-normalized, BGR→RGB |
| Output | Deepfake probability ∈ [0, 1]; authenticity = (1 − p) × 100 |
| Checkpoint | `models/spatial_probe.pt` (backup: `spatial_probe_v1_98acc.pt`) |

**Why DINOv2 + linear probe:** DINOv2 is self-supervised on a large image corpus, so
its features capture fine-grained texture and structure. Face-generation models leave
subtle spatial inconsistencies these features expose. Freezing the backbone and training
only the probe is data-efficient (minutes on an M4), reproducible, and resistant to
overfitting.

---

## 3. Performance

FaceForensics++ evaluation — 200 real / 200 fake videos (c23):

| Metric | Value |
|--------|-------|
| Accuracy | **97.8%** |
| AUC-ROC | **0.998** |
| F1 | **0.978** |

Held-out backend check (real `SpatialDetector`, sampled clips): **98.0%**
(real videos mean prob ≈ 0.04, fake videos mean prob ≈ 0.93).

Reproduce: `notebooks/01_model_training.ipynb` (train) → `notebooks/02_benchmark_eval.ipynb` (evaluate).

---

## 4. Forensic Reasoning (Feedback Analysis)

The Forensic Reasoning Engine builds a context from the detection result and evidence,
retrieves relevant research from ChromaDB, and asks **Llama 3.2 (local Ollama,
`/api/chat`)** for a structured forensic brief:

- **SUMMARY** — overall verdict
- **KEY FINDINGS** — spatial evidence markers
- **TECHNICAL ANALYSIS** — DINOv2 spatial findings
- **CITED RESEARCH** — retrieved papers
- **CONFIDENCE ASSESSMENT** — calibrated confidence + caveats

No API key, no network egress. If Ollama is unavailable, a deterministic
template-based explanation is returned.

Config (`.env`):
```
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

---

## 5. Pipeline

```
upload → frame extraction → DINOv2 spatial probe → authenticity score + evidence
       → RAG retrieval → Llama 3.2 forensic brief → response
```

API:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/analyze` | Full spatial analysis + forensic reasoning |
| POST | `/api/analyze/quick` | Fast spatial check |
| POST | `/api/analyze/stream` | SSE streaming with progress |
| POST | `/api/rag/ingest` | Ingest research papers |
| GET  | `/api/rag/search?q=...` | Search knowledge base |
| GET  | `/api/health` | Health check |

Response (`/api/analyze`): `authenticity_score`, `deepfake_probability`,
`confidence_level`, `evidence[]`, `explanation`, `processing_time_sec`.

---

## 6. Scope & Limitations

- **Spatial only.** Detection relies on per-frame texture and structural artifacts
  extracted by the DINOv2 probe.
- Performance reflects the FaceForensics++ (c23) training distribution. Heavy
  compression and out-of-distribution generators reduce accuracy.
- A "fake"/"real" verdict is a probabilistic assessment, not proof. Cross-reference for
  high-stakes decisions.

---

## 7. How to Run

```bash
# 1. Local LLM
ollama pull llama3.2 && ollama serve

# 2. Backend
source .venv/bin/activate
python -m backend.main          # http://localhost:8000

# 3. Frontend
cd frontend && npm install && npm run dev   # http://localhost:3000
```
