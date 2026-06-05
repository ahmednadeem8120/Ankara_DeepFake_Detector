from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
import numpy as np


@dataclass
class EvidenceMarker:
    timestamp_sec: float
    frame_index: int
    artifact_type: str
    description: str
    confidence: float
    region: Optional[dict] = None
    heatmap: Optional[np.ndarray] = None


@dataclass
class DetectionResult:
    module_name: str
    fake_probability: float
    confidence: float
    evidence: list[EvidenceMarker] = field(default_factory=list)
    heatmap: Optional[np.ndarray] = None
    metadata: dict = field(default_factory=dict)


class BaseDetector(ABC):
    def __init__(self, device: str = "cpu"):
        self.device = device
        self.model = None
        self._loaded = False

    @abstractmethod
    def load_model(self) -> None: ...

    @abstractmethod
    def detect_image(self, image: np.ndarray) -> DetectionResult: ...

    @abstractmethod
    def detect_video(self, frames: list[np.ndarray], fps: float) -> DetectionResult: ...

    def ensure_loaded(self) -> None:
        if not self._loaded:
            self.load_model()
            self._loaded = True
