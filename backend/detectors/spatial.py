import numpy as np
import torch
import torch.nn as nn
from torchvision import transforms

from .base import BaseDetector, DetectionResult, EvidenceMarker


class DINOv2Probe(nn.Module):
    # Architecture must stay in sync with spatial_probe.pt (97.8% / 0.998 AUC).
    def __init__(self, feature_dim: int = 768):
        super().__init__()
        self.probe = nn.Sequential(
            nn.LayerNorm(feature_dim),
            nn.Linear(feature_dim, 128),
            nn.GELU(),
            nn.Dropout(0.2),
            nn.Linear(128, 1),
            nn.Sigmoid(),
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.probe(features)


class SpatialDetector(BaseDetector):
    MODULE_NAME = "spatial"

    def __init__(self, device: str = "cpu"):
        super().__init__(device)
        self.dino_model = None
        self.dino_probe = None
        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def load_model(self) -> None:
        from transformers import AutoModel
        from pathlib import Path

        self.dino_model = AutoModel.from_pretrained("facebook/dinov2-base")
        self.dino_model.eval()
        self.dino_model.to(self.device)
        for param in self.dino_model.parameters():
            param.requires_grad = False

        self.dino_probe = DINOv2Probe(feature_dim=768).to(self.device)

        probe_path = Path(__file__).resolve().parent.parent.parent / "models" / "spatial_probe.pt"
        if probe_path.exists():
            state_dict = torch.load(probe_path, map_location=self.device, weights_only=True)
            self.dino_probe.load_state_dict(state_dict, strict=True)
            print(f"[Ankara] Loaded DINOv2 probe — {sum(p.numel() for p in self.dino_probe.parameters())} params")
        else:
            print("[Ankara] WARNING: spatial_probe.pt not found — using random probe weights")

        self.dino_probe.eval()
        self._loaded = True

    def _extract_dino_features(self, image: np.ndarray) -> torch.Tensor:
        img_rgb = image[:, :, ::-1] if image.shape[2] == 3 else image  # BGR→RGB
        tensor = self.transform(img_rgb.copy()).unsqueeze(0).to(self.device)
        with torch.no_grad():
            features = self.dino_model(tensor).last_hidden_state[:, 0]
        return features

    def detect_image(self, image: np.ndarray) -> DetectionResult:
        self.ensure_loaded()
        features = self._extract_dino_features(image)
        fake_prob = self.dino_probe(features).item()
        confidence = max(0.1, min(1.0, abs(fake_prob - 0.5) * 2))
        evidence = []
        if fake_prob > 0.6:
            evidence.append(EvidenceMarker(
                timestamp_sec=0.0,
                frame_index=0,
                artifact_type="texture_anomaly",
                description=f"DINOv2 detected spatial texture inconsistencies (score: {fake_prob:.2f})",
                confidence=fake_prob,
            ))
        return DetectionResult(
            module_name=self.MODULE_NAME,
            fake_probability=fake_prob,
            confidence=confidence,
            evidence=evidence,
            metadata={"dino_score": fake_prob},
        )

    def detect_video(self, frames: list[np.ndarray], fps: float) -> DetectionResult:
        self.ensure_loaded()
        all_evidence = []
        scores = []
        sample_indices = np.linspace(0, len(frames) - 1, min(16, len(frames)), dtype=int)
        for idx in sample_indices:
            frame_result = self.detect_image(frames[idx])
            scores.append(frame_result.fake_probability)
            for ev in frame_result.evidence:
                ev.timestamp_sec = idx / fps
                ev.frame_index = int(idx)
                all_evidence.append(ev)
        avg_score = float(np.mean(scores))
        return DetectionResult(
            module_name=self.MODULE_NAME,
            fake_probability=avg_score,
            confidence=max(0.1, abs(avg_score - 0.5) * 2),
            evidence=all_evidence,
            metadata={
                "frames_analyzed": len(sample_indices),
                "per_frame_scores": [round(s, 3) for s in scores],
            },
        )
