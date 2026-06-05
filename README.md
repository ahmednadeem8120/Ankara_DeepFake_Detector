# ANKARA — Deepfake Detection Platform

> **DINOv2 spatial probe · RAG forensic reasoning · Local Llama 3.2 · Next.js UI**

Ankara detects deepfakes using a linear probe on frozen **DINOv2-base** vision transformer features, validated at **97.8% accuracy / 0.998 AUC** on FaceForensics++. Detection results are explained by a local **Llama 3.2** model (via Ollama) grounded in a ChromaDB research knowledge base — no API key required.

---

## Demo

| Real media | Deepfake |
|---|---|
| Authenticity Score: **95%** · Confidence: High | Authenticity Score: **7%** · Confidence: High |

---

## Architecture

```
Upload (image / video)
    ↓
DINOv2-base (frozen ViT backbone)
    → CLS feature → linear probe (768→128→1)
    → deepfake probability
    ↓
RAG retrieval (ChromaDB)
    ↓
Llama 3.2 (local Ollama)
    → structured forensic brief
    ↓
Next.js dashboard
```

---

## Performance

Evaluated on FaceForensics++ (c23), 200 real / 200 fake videos:

| Metric | Score |
|--------|-------|
| Accuracy | **97.8%** |
| AUC-ROC | **0.998** |
| F1 | **0.978** |

---

## Stack

| Layer | Technology |
|-------|-----------|
| Detection backbone | `facebook/dinov2-base` (frozen) |
| Probe | PyTorch linear head (100K params) |
| API | FastAPI + Uvicorn |
| Forensic reasoning | Llama 3.2 via local Ollama |
| Knowledge base | ChromaDB + sentence-transformers |
| Frontend | Next.js 14 · Tailwind CSS · Framer Motion |

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

cp .env.example .env        # already configured for Ollama
python -m backend.main      # → http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev                 # → http://localhost:3000
```

Upload an image or video and hit **Run Forensic Analysis**.

---

## Training Your Own Probe

The DINOv2 backbone is always frozen. Only the small linear head trains.

1. Place labelled clips under `datasets/train_subset/{real,fake}/`
2. Run `notebooks/01_model_training.ipynb` (~5 min on M-series Mac)
3. Evaluate with `notebooks/02_benchmark_eval.ipynb`

Weights save to `models/spatial_probe.pt`.

---

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/analyze` | Full analysis + forensic reasoning |
| `POST` | `/api/analyze/quick` | Fast spatial check |
| `POST` | `/api/analyze/stream` | SSE streaming with live progress |
| `POST` | `/api/rag/ingest` | Ingest a research paper (.pdf/.md/.txt) |
| `GET` | `/api/rag/search?q=...` | Search the knowledge base |
| `GET` | `/api/health` | Health check |

---

## Project Structure

```
├── backend/
│   ├── main.py                  # FastAPI app
│   ├── config.py                # Settings (Pydantic)
│   ├── detectors/
│   │   ├── base.py              # Abstract detector
│   │   └── spatial.py           # DINOv2 probe
│   ├── rag/
│   │   ├── ingest.py            # Paper ingestion
│   │   ├── retriever.py         # Semantic search
│   │   └── explainer.py         # Forensic reasoning engine
│   └── utils/
│       └── preprocessing.py     # Frame extraction
├── frontend/
│   ├── app/page.tsx             # Upload + results UI
│   └── components/              # Dashboard, timeline, explainer
├── notebooks/
│   ├── 01_model_training.ipynb  # Probe training
│   └── 02_benchmark_eval.ipynb  # Benchmark evaluation
├── models/                      # spatial_probe.pt (gitignored)
├── requirements.txt
└── .env.example
```

---

## Limitations

- Spatial detection only — relies on per-frame texture artifacts
- Performance reflects FaceForensics++ (c23) training distribution
- No audio track analysis (FaceForensics++ is video-only)

---

## References

- Oquab et al. *DINOv2: Learning Robust Visual Features without Supervision.* 2023
- Rossler et al. *FaceForensics++.* ICCV 2019
- Dolhansky et al. *The DeepFake Detection Challenge Dataset.* 2020

---

## License

MIT — Ahmed Nadeem, University of West London, 2025
