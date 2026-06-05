# ANKARA — Deepfake Detection Platform

> DINOv2 spatial probe · RAG forensic reasoning · Local Llama 3.2 · Next.js UI

Ankara is a full-stack deepfake detection system. A linear probe trained on frozen DINOv2-base vision transformer features classifies video frames as real or manipulated, achieving **97.8% accuracy and 0.998 AUC-ROC** on FaceForensics++ (c23). Detection results are explained by a local Llama 3.2 model grounded in a ChromaDB research knowledge base — no API key or cloud dependency required.

---

## How It Works

```
Upload (image / video)
        │
        ▼
┌─────────────────────────────────────────┐
│           Preprocessing Layer           │
│   Frame extraction · Face detection     │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│         Spatial Detection Layer         │
│                                         │
│   DINOv2-base (frozen, 87M params)      │
│     → CLS token feature (768-dim)       │
│   Linear probe (768 → 128 → 1)          │
│     → deepfake probability per frame    │
│   Average across 16 sampled frames      │
│     → final video score                 │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│           RAG Knowledge Layer           │
│   ChromaDB · sentence-transformers      │
│   Retrieves relevant research papers    │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│        Forensic Reasoning Engine        │
│   Local Llama 3.2 via Ollama            │
│   Generates structured forensic brief   │
│   grounded in retrieved research        │
└──────────────────┬──────────────────────┘
                   │
                   ▼
         Next.js Dashboard
   Authenticity score · Evidence timeline
   Confidence · Forensic explanation
```

The DINOv2 backbone is always frozen — only the 100K-parameter probe head trains. This makes training data-efficient (minutes on an M-series Mac), fast at inference, and resistant to overfitting. Face-generation models leave subtle spatial inconsistencies in texture and structure that DINOv2's self-supervised features expose effectively.

The RAG layer is what separates Ankara from a plain classifier. Rather than returning a score and nothing else, it retrieves relevant forensic research and uses a local LLM to explain *why* a video was flagged in plain language — no black box.

---

## Performance

*Probe trained on FaceForensics++ (c23). Evaluated on 200 real + 200 fake held-out videos.*

| Method | Accuracy | AUC-ROC | F1 |
|--------|----------|---------|-----|
| **Ankara (DINOv2 spatial probe)** | **97.8%** | **0.998** | **0.978** |
| XceptionNet (Rossler et al. 2019) | 95.7% | 0.981 | 0.957 |
| EfficientNet-B4 | 96.1% | 0.985 | 0.961 |

Reproduce with `notebooks/02_benchmark_eval.ipynb`.

---

## Stack

| Layer | Technology |
|-------|-----------|
| Detection backbone | `facebook/dinov2-base` (frozen ViT) |
| Probe | PyTorch linear head — 100K trainable params |
| API | FastAPI + Uvicorn + SSE streaming |
| Forensic reasoning | Llama 3.2 via local Ollama |
| Knowledge base | ChromaDB + sentence-transformers |
| Frontend | Next.js 14 · Tailwind CSS · Framer Motion |
| Training | PyTorch · HuggingFace Transformers · FF++ dataset |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- [Ollama](https://ollama.com) with Llama 3.2

```bash
ollama pull llama3.2
ollama serve
```

### Backend

```bash
git clone https://github.com/ahmednadeem8120/Ankara_DeepFake_Detector.git
cd Ankara_DeepFake_Detector

python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env        # pre-configured for local Ollama — no keys needed
python -m backend.main      # → http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev                 # → http://localhost:3000
```

Open `http://localhost:3000`, upload an image or video and click **Run Forensic Analysis**.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/analyze` | Full spatial analysis + forensic reasoning |
| `POST` | `/api/analyze/quick` | Fast spatial check only |
| `POST` | `/api/analyze/stream` | SSE streaming with live progress |
| `POST` | `/api/rag/ingest` | Ingest a research paper (`.pdf` / `.md` / `.txt`) |
| `GET` | `/api/rag/search?q=...` | Search the knowledge base |
| `GET` | `/api/health` | Health check |

---

## Training Your Own Probe

The DINOv2 backbone is always frozen. Only the small linear head trains.

1. Request FaceForensics++ access at [github.com/ondyari/FaceForensics](https://github.com/ondyari/FaceForensics)
2. Place labelled clips under `datasets/train_subset/{real,fake}/`
3. Run `notebooks/01_model_training.ipynb` — ~5 minutes on M-series Mac
4. Evaluate with `notebooks/02_benchmark_eval.ipynb`
5. Weights save to `models/spatial_probe.pt`

For per-method generalisation analysis across all FF++ manipulation methods (Deepfakes, Face2Face, FaceShifter, FaceSwap, NeuralTextures, DeepFakeDetection), run `notebooks/03_ffpp_per_method_eval.ipynb`.

---

## Project Structure

```
├── backend/
│   ├── main.py                        # FastAPI application
│   ├── config.py                      # Pydantic settings
│   ├── detectors/
│   │   ├── base.py                    # Abstract detector interface
│   │   └── spatial.py                 # DINOv2 spatial probe
│   ├── rag/
│   │   ├── ingest.py                  # Paper ingestion pipeline
│   │   ├── retriever.py               # Semantic search
│   │   └── explainer.py               # Forensic Reasoning Engine
│   └── utils/
│       └── preprocessing.py           # Frame extraction
├── frontend/
│   ├── app/
│   │   ├── page.tsx                   # Upload + results UI
│   │   ├── layout.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── TrustScoreDashboard.tsx
│   │   ├── EvidenceTimeline.tsx
│   │   ├── AnalysisProgress.tsx
│   │   └── ForensicExplainer.tsx
│   └── lib/api.ts                     # TypeScript API client
├── notebooks/
│   ├── 01_model_training.ipynb        # Probe training
│   ├── 02_benchmark_eval.ipynb        # FF++ benchmark evaluation
│   └── 03_ffpp_per_method_eval.ipynb  # Per-method generalisation eval
├── models/
│   └── spatial_probe.pt               # Trained probe weights
├── docs/
│   ├── benchmark.png                  # Confusion matrix + score distribution
│   ├── training_curves.png            # Loss + validation accuracy
│   └── REPORT.md                      # Technical report
├── MODEL_CARD.md
├── requirements.txt
└── .env.example
```

---

## Limitations

- **Spatial detection only** — relies on per-frame texture artifacts; no audio or temporal analysis
- **Designed for talking-head format video** — face should be the dominant element in frame, consistent with FF++ face-crop evaluation protocol. Raw broadcast or wide-shot video requires upstream face extraction (MTCNN recommended)
- **Training distribution** — performance reflects FaceForensics++ (c23); cross-dataset generalisation to newer generation methods (post-2022) is limited and documented in `MODEL_CARD.md`
- **No adversarial robustness evaluation** — the probe has not been tested against attacks designed to evade it

---

## References

- Oquab et al. *DINOv2: Learning Robust Visual Features without Supervision.* 2023
- Rossler et al. *FaceForensics++: Learning to Detect Manipulated Facial Images.* ICCV 2019
- Dolhansky et al. *The DeepFake Detection Challenge Dataset.* 2020

---

## License

MIT — Ahmed Nadeem, University of West London, 2026
