import uuid
import time
import asyncio
from pathlib import Path
from typing import Optional

import cv2
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

from .config import settings
from .detectors.spatial import SpatialDetector
from .detectors.base import DetectionResult
from .rag.ingest import PaperIngester
from .rag.explainer import ForensicReasoningEngine
from .utils.preprocessing import get_media_info, extract_frames


app = FastAPI(title="Ankara", description="DINOv2 Spatial Deepfake Detection", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnkaraState:
    def __init__(self):
        self._spatial = None
        self._explainer = None
        self._ingester = None

    @property
    def spatial(self) -> SpatialDetector:
        if self._spatial is None:
            self._spatial = SpatialDetector(device=settings.DEVICE)
        return self._spatial

    @property
    def explainer(self) -> ForensicReasoningEngine:
        if self._explainer is None:
            self._explainer = ForensicReasoningEngine()
        return self._explainer

    @property
    def ingester(self) -> PaperIngester:
        if self._ingester is None:
            self._ingester = PaperIngester()
        return self._ingester


state = AnkaraState()


def _confidence_level(result: DetectionResult) -> str:
    prob = result.fake_probability
    if result.confidence > 0.7 and abs(prob - 0.5) > 0.3:
        return "high"
    if result.confidence > 0.4:
        return "medium"
    return "low"


def shape_result(result: DetectionResult, request_id: str) -> dict:
    return {
        "request_id": request_id,
        "authenticity_score": round((1.0 - result.fake_probability) * 100, 1),
        "deepfake_probability": round(result.fake_probability, 3),
        "confidence_level": _confidence_level(result),
        "evidence": [
            {
                "timestamp_sec": round(e.timestamp_sec, 2),
                "frame_index": e.frame_index,
                "artifact_type": e.artifact_type,
                "description": e.description,
                "confidence": round(e.confidence, 3),
            }
            for e in result.evidence
        ],
        "metadata": result.metadata,
    }


@app.on_event("startup")
async def startup():
    try:
        result = state.ingester.ingest_builtin_knowledge()
        print(f"[Ankara] RAG initialized: {result}")
    except Exception as e:
        print(f"[Ankara] RAG init skipped: {e}")


class AnalysisResponse(BaseModel):
    request_id: str
    media_type: str
    authenticity_score: float
    deepfake_probability: float
    confidence_level: str
    evidence: list
    explanation: Optional[str] = None
    processing_time_sec: float


@app.get("/api/health")
async def health_check():
    return {
        "status": "operational",
        "platform": "Ankara v2.0",
        "device": settings.DEVICE,
        "model": "DINOv2 spatial probe",
        "rag_enabled": True,
    }


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_media(file: UploadFile = File(...)):
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    suffix = Path(file.filename).suffix.lower()
    upload_path = settings.UPLOAD_DIR / f"{request_id}{suffix}"
    with open(upload_path, "wb") as f:
        f.write(await file.read())

    try:
        media_info = get_media_info(str(upload_path))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        if media_info.media_type == "image":
            image = cv2.imread(str(upload_path))
            if image is None:
                raise HTTPException(status_code=400, detail="Could not read image")
            result = state.spatial.detect_image(image)
        else:
            frames = extract_frames(str(upload_path))
            if not frames:
                raise HTTPException(status_code=400, detail="Could not extract frames")
            result = state.spatial.detect_video(frames, media_info.fps)
    finally:
        upload_path.unlink(missing_ok=True)

    shaped = shape_result(result, request_id)

    try:
        explanation = await state.explainer.explain_async(shaped)
    except Exception as e:
        explanation = f"Explanation generation failed: {e}"

    return AnalysisResponse(
        request_id=request_id,
        media_type=media_info.media_type,
        authenticity_score=shaped["authenticity_score"],
        deepfake_probability=shaped["deepfake_probability"],
        confidence_level=shaped["confidence_level"],
        evidence=shaped["evidence"],
        explanation=explanation,
        processing_time_sec=round(time.time() - start_time, 2),
    )


@app.post("/api/analyze/quick")
async def quick_analyze(file: UploadFile = File(...)):
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    suffix = Path(file.filename).suffix.lower()
    upload_path = settings.UPLOAD_DIR / f"{request_id}{suffix}"
    with open(upload_path, "wb") as f:
        f.write(await file.read())

    try:
        image = cv2.imread(str(upload_path))
        if image is None:
            raise HTTPException(status_code=400, detail="Could not read image")
        result = state.spatial.detect_image(image)
        return {
            "request_id": request_id,
            "deepfake_probability": round(result.fake_probability, 3),
            "confidence": round(result.confidence, 3),
            "evidence_count": len(result.evidence),
            "processing_time_sec": round(time.time() - start_time, 3),
        }
    finally:
        upload_path.unlink(missing_ok=True)


@app.post("/api/analyze/stream")
async def stream_analysis(file: UploadFile = File(...)):
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    suffix = Path(file.filename).suffix.lower()
    upload_path = settings.UPLOAD_DIR / f"{request_id}{suffix}"
    with open(upload_path, "wb") as f:
        f.write(await file.read())

    async def event_stream():
        try:
            media_info = get_media_info(str(upload_path))

            yield _sse("progress", {"step": "preprocessing", "progress": 15})
            await asyncio.sleep(0.05)

            yield _sse("progress", {"step": "spatial_analysis", "progress": 45})
            if media_info.media_type == "image":
                image = cv2.imread(str(upload_path))
                result = state.spatial.detect_image(image)
            else:
                frames = extract_frames(str(upload_path))
                result = state.spatial.detect_video(frames, media_info.fps)

            shaped = shape_result(result, request_id)
            yield _sse("module_complete", {
                "module": "spatial",
                "deepfake_probability": shaped["deepfake_probability"],
            })

            yield _sse("progress", {"step": "explanation", "progress": 80})
            try:
                explanation = state.explainer.explain(shaped)
            except Exception:
                explanation = None

            yield _sse("progress", {"step": "complete", "progress": 100})
            yield _sse("result", {
                **shaped,
                "media_type": media_info.media_type,
                "explanation": explanation,
                "processing_time_sec": round(time.time() - start_time, 2),
            })

        except Exception as e:
            yield _sse("error", {"message": str(e)})
        finally:
            upload_path.unlink(missing_ok=True)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@app.post("/api/rag/ingest")
async def ingest_papers(file: UploadFile = File(...)):
    suffix = Path(file.filename).suffix.lower()
    if suffix not in (".pdf", ".md", ".txt"):
        raise HTTPException(status_code=400, detail="Supported formats: .pdf, .md, .txt")
    upload_path = settings.PAPERS_DIR / file.filename
    with open(upload_path, "wb") as f:
        f.write(await file.read())
    return state.ingester.ingest_file(str(upload_path))


@app.get("/api/rag/search")
async def search_knowledge(q: str, n: int = 5):
    results = state.explainer.retriever.retrieve(q, n_results=n)
    return {"query": q, "results": results}


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)
