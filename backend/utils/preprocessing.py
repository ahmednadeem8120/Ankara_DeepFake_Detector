import cv2
import numpy as np
from pathlib import Path
from dataclasses import dataclass

from ..config import settings


@dataclass
class MediaInfo:
    filepath: str
    media_type: str
    width: int
    height: int
    fps: float
    total_frames: int
    duration_sec: float
    has_audio: bool


def get_media_info(filepath: str) -> MediaInfo:
    path = Path(filepath)
    suffix = path.suffix.lower()

    if suffix in (".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"):
        img = cv2.imread(filepath)
        if img is None:
            raise ValueError(f"Could not read image: {filepath}")
        h, w = img.shape[:2]
        return MediaInfo(filepath=filepath, media_type="image", width=w, height=h,
                         fps=0, total_frames=1, duration_sec=0, has_audio=False)

    elif suffix in (".mp4", ".avi", ".mov", ".mkv", ".webm"):
        cap = cv2.VideoCapture(filepath)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {filepath}")
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        has_audio = _check_audio_track(filepath)
        return MediaInfo(filepath=filepath, media_type="video", width=w, height=h,
                         fps=fps, total_frames=total,
                         duration_sec=total / fps if fps > 0 else 0, has_audio=has_audio)

    else:
        raise ValueError(f"Unsupported file format: {suffix}")


def _check_audio_track(filepath: str) -> bool:
    try:
        import subprocess
        result = subprocess.run(
            ["ffprobe", "-i", filepath, "-show_streams", "-select_streams", "a", "-loglevel", "error"],
            capture_output=True, text=True, timeout=10,
        )
        return len(result.stdout.strip()) > 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def extract_frames(filepath: str, max_frames: int = None, sample_rate: int = None) -> list[np.ndarray]:
    max_frames = max_frames or settings.MAX_FRAMES
    sample_rate = sample_rate or settings.FRAME_SAMPLE_RATE

    cap = cv2.VideoCapture(filepath)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {filepath}")

    frames = []
    frame_idx = 0
    while cap.isOpened() and len(frames) < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % sample_rate == 0:
            frames.append(frame)
        frame_idx += 1

    cap.release()
    return frames
