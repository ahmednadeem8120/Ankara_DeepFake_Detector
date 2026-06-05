# Model Card: Ankara Deepfake Detection System

## Model Details

**Name:** Ankara DINOv2 Spatial Deepfake Detector
**Version:** 2.0
**Type:** Binary classifier (real vs. manipulated)
**Architecture:** Linear probe on a frozen DINOv2-base vision transformer
**Developer:** Ahmed (University of West London)
**Date:** 2025

### Components

| Component | Architecture | Parameters | Input |
|-----------|-------------|------------|-------|
| Backbone | DINOv2-base (frozen ViT) | ~87M (frozen) | Image 224×224 |
| Probe | LayerNorm → Linear(768→128) → GELU → Dropout → Linear(128→1) → Sigmoid | ~100K (trained) | DINOv2 CLS feature |
| Reasoning | Llama 3.2 (local, via Ollama) + ChromaDB RAG | — | Detection result |

For video, the probe scores up to 16 evenly-sampled full frames and averages the
per-frame deepfake probabilities.

## Intended Use

**Primary:** Research tool and portfolio demonstration of self-supervised deepfake
detection. Intended for analysis of uploaded images and videos in a controlled setting.

**In scope:**
- Detecting face-swap and face-reenactment deepfakes (e.g. FaceForensics++ methods)
- Providing forensic explanations grounded in research

**Out of scope:**
- Production content-moderation at scale
- Legal evidence or forensic testimony
- Non-face synthesis, voice cloning, or text generation
- Real-time streaming detection at scale

## Training Data

**Dataset:** FaceForensics++ (Rossler et al., 2019)
- 1,000 original videos + face-manipulation methods
- c23 (light compression) used for the probe training subset

**Augmentation:** horizontal flip. The frozen backbone provides most of the
robustness; the probe only learns a decision boundary over its features.

## Performance

FaceForensics++ evaluation (200 real / 200 fake videos, c23):

| Metric | Value |
|--------|-------|
| Accuracy | 97.8% |
| AUC-ROC | 0.998 |
| F1 Score | 0.978 |

Reproduce with `notebooks/02_benchmark_eval.ipynb`.

### Known Performance Gaps

**By compression:** Spatial-domain detection degrades under heavy compression (c40),
where texture artifacts are partially destroyed.

**By demographics:** FaceForensics++ has demographic imbalance; accuracy may be lower
for underrepresented groups. Evaluate on diverse data before any deployment.

**By face size / occlusion:** Very small or heavily occluded faces reduce reliability.

**By generation method:** The probe generalizes across the manipulation methods seen in
training, but novel post-training-date generators may evade detection.

## Ethical Considerations

**Dual-use risk:** Detection systems can be used to improve generators via adversarial
feedback. This system is intended for defensive analysis only.

**False positives:** A "fake" prediction is not proof of manipulation. Compression,
re-encoding, and unusual lighting can trigger false positives.

**False negatives:** A "real" prediction does not guarantee authenticity. Novel methods
and adversarial post-processing can evade detection.

**Privacy:** The system processes facial imagery. In production, process data
ephemerally and do not store it.

## Limitations

1. Detection is **spatial only** — it relies on per-frame texture and structural
   artifacts extracted by the DINOv2 probe.
2. Performance reflects the FaceForensics++ training distribution; cross-dataset
   generalization should be evaluated before use.
3. The Forensic Reasoning Engine runs on a local Llama 3.2 model via Ollama; if Ollama
   is unavailable it falls back to a template-based explanation.
4. The system has not been evaluated against adversarial attacks designed to evade it.

## Recommendations

- Treat outputs as probabilistic assessments, not definitive judgments
- Cross-reference with other tools for high-stakes decisions
- Retrain the probe periodically as new generation methods emerge
- Evaluate on demographically diverse datasets before any deployment
- Do not use for automated content removal without human review
