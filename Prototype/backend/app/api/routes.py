from __future__ import annotations

import base64
import time
from typing import Any, Dict, List, Optional

import cv2
import os
from pathlib import Path

from fastapi import APIRouter, Depends, File, Query, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, Response
from sqlmodel import Session, select

from app.db.models import DetectionRun, Job, MediaAsset
from app.db.session import get_session
from app.api.deps import get_current_user
from app.db.models import User
from app.ml.infer import (
    bgr_to_jpeg_bytes,
    bytes_to_bgr,
    decode_base64_jpeg,
    detect_image_bytes,
    draw_detections_bgr,
    sha256_bytes,
)
from app.ml.model_registry import ModelName, supported_models
from app.schemas.detect import DetectResponse, DetectionItem, Box
from app.services.persistence import create_asset, create_run, insert_detections
from app.core.config import get_settings
from app.tasks.video_jobs import process_video_job
from app.services.storage import put_bytes, get_bytes

router = APIRouter()


def _to_response(model: str, device: str, processing_ms: int, dets, asset_id: Optional[int], run_id: Optional[int]):
    return DetectResponse(
        model=model,
        device=device,
        processing_ms=processing_ms,
        asset_id=asset_id,
        run_id=run_id,
        detections=[
            DetectionItem(label=d.label, score=d.score, box=Box(x1=d.x1, y1=d.y1, x2=d.x2, y2=d.y2)) for d in dets
        ],
    )


@router.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True}


@router.get("/models")
def list_models() -> Dict[str, Any]:
    return {"supported": supported_models()}


@router.post("/detect/image", response_model=DetectResponse)
async def detect_image(
    model: ModelName = Query("yolo"),
    score_thresh: float = Query(0.25, ge=0.0, le=1.0),
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    content = await file.read()
    dets, processing_ms, device = detect_image_bytes(model, content, score_thresh=score_thresh)

    settings = get_settings()
    img_bgr = bytes_to_bgr(content)
    ann = draw_detections_bgr(img_bgr, dets)
    ann_bytes = bgr_to_jpeg_bytes(ann, quality=85)
    stored = put_bytes(kind="artifacts", filename=f"img-{int(time.time()*1000)}.jpg", data=ann_bytes)

    asset = create_asset(
        session,
        kind="image",
        filename=file.filename or "upload",
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(content),
        sha256=sha256_bytes(content),
    )
    run = create_run(
        session,
        asset_id=asset.id,
        model_name=model,
        device=device,
        processing_ms=processing_ms,
        user_id=user.id,
        artifact_path=stored.object_key if stored.storage == "local" else None,
        artifact_storage=stored.storage,
        artifact_object_key=stored.object_key if stored.storage == "s3" else None,
    )
    insert_detections(session, run_id=run.id, dets=dets)
    return _to_response(model, device, processing_ms, dets, asset.id, run.id)


@router.post("/detect/video")
async def detect_video(
    model: ModelName = Query("yolo"),
    score_thresh: float = Query(0.25, ge=0.0, le=1.0),
    max_frames: int = Query(300, ge=1, le=5000),
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Queues an async video job and returns a job id."""
    blob = await file.read()
    safe_name = file.filename or "video.mp4"
    stored_media = put_bytes(kind="media", filename=f"{int(time.time()*1000)}-{safe_name}", data=blob)

    asset = create_asset(
        session,
        kind="video",
        filename=stored_media.object_key,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(blob),
        sha256=sha256_bytes(blob),
        storage=stored_media.storage,
        object_key=stored_media.object_key if stored_media.storage == "s3" else None,
    )

    job = Job(
        user_id=user.id,
        kind="video",
        status="queued",
        model_name=model,
        score_thresh=score_thresh,
        asset_id=asset.id,
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    celery_result = process_video_job.delay(job.id, max_frames=max_frames)
    return {"job_id": job.id, "celery_task_id": celery_result.id, "asset_id": asset.id}


@router.get("/jobs/{job_id}")
def get_job(job_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)) -> Dict[str, Any]:
    job = session.get(Job, job_id)
    if not job or (job.user_id != user.id and user.role != "admin"):
        return {"error": "not found"}
    return {
        "id": job.id,
        "status": job.status,
        "model_name": job.model_name,
        "score_thresh": job.score_thresh,
        "asset_id": job.asset_id,
        "run_id": job.run_id,
        "error": job.error,
        "created_at": job.created_at.isoformat(),
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
    }


@router.get("/jobs")
def list_jobs(
    mine: bool = True,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    page = max(1, page)
    page_size = min(max(1, page_size), 100)

    stmt = select(Job).order_by(Job.created_at.desc())
    if mine:
        stmt = stmt.where(Job.user_id == user.id)
    else:
        if user.role != "admin":
            return {"error": "admin required"}
    if status:
        stmt = stmt.where(Job.status == status)

    # SQLModel doesn't provide count easily without extra query; do a best-effort window via over-fetch.
    offset = (page - 1) * page_size
    rows = session.exec(stmt.offset(offset).limit(page_size + 1)).all()
    has_next = len(rows) > page_size
    rows = rows[:page_size]
    return {
        "page": page,
        "page_size": page_size,
        "has_next": has_next,
        "jobs": [
            {
                "id": j.id,
                "status": j.status,
                "model_name": j.model_name,
                "asset_id": j.asset_id,
                "run_id": j.run_id,
                "error": j.error,
                "created_at": j.created_at.isoformat(),
            }
            for j in rows
        ],
    }


@router.get("/runs/{run_id}/download")
def download_artifact(run_id: int, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    run = session.get(DetectionRun, run_id)
    if not run or (run.user_id != user.id and user.role != "admin"):
        return {"error": "not found"}
    # local artifact
    if run.artifact_storage == "local" and run.artifact_path:
        p = Path(run.artifact_path)
        if not p.exists():
            return {"error": "artifact missing"}
        media_type = "application/octet-stream"
        if p.suffix.lower() in (".jpg", ".jpeg"):
            media_type = "image/jpeg"
        if p.suffix.lower() == ".mp4":
            media_type = "video/mp4"
        return FileResponse(path=str(p), filename=p.name, media_type=media_type)

    # s3 artifact (stream as bytes; ok for reference, use StreamingResponse for very large objects)
    if run.artifact_storage == "s3" and run.artifact_object_key:
        data = get_bytes(storage="s3", object_key=run.artifact_object_key)
        fn = os.path.basename(run.artifact_object_key)
        media_type = "application/octet-stream"
        if fn.lower().endswith((".jpg", ".jpeg")):
            media_type = "image/jpeg"
        if fn.lower().endswith(".mp4"):
            media_type = "video/mp4"
        return Response(content=data, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="{fn}"'})

    return {"error": "artifact missing"}


@router.get("/metrics/recent")
def recent_runs(limit: int = 50, session: Session = Depends(get_session)) -> Dict[str, Any]:
    rows = session.exec(select(DetectionRun).order_by(DetectionRun.created_at.desc()).limit(limit)).all()
    return {
        "runs": [
            {
                "id": r.id,
                "asset_id": r.asset_id,
                "model_name": r.model_name,
                "device": r.device,
                "processing_ms": r.processing_ms,
                "fps": r.fps,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ]
    }


@router.get("/models/compare")
def compare_models(session: Session = Depends(get_session)) -> Dict[str, Any]:
    """
    Comparison here is based on stored `DetectionRun` performance metrics (processing_ms/fps).
    mAP/IoU require a labeled dataset; see `/metrics` docs in README for offline evaluation workflow.
    """
    rows = session.exec(select(DetectionRun)).all()
    agg: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        m = r.model_name
        a = agg.setdefault(m, {"count": 0, "avg_processing_ms": 0.0, "avg_fps": None})
        a["count"] += 1
        a["avg_processing_ms"] += float(r.processing_ms)
        if r.fps is not None:
            if a["avg_fps"] is None:
                a["avg_fps"] = 0.0
            a["avg_fps"] += float(r.fps)
    for m, a in agg.items():
        if a["count"] > 0:
            a["avg_processing_ms"] = a["avg_processing_ms"] / a["count"]
            if a["avg_fps"] is not None:
                a["avg_fps"] = a["avg_fps"] / a["count"]
    return {"by_model": agg, "supported": supported_models()}


@router.get("/metrics")
def metrics_help() -> Dict[str, Any]:
    return {
        "note": "Online mAP/IoU require ground-truth labels. This reference system stores runtime stats (processing_ms/fps) per run. Add an offline evaluation job to compute mAP/IoU/precision/recall/F1 on a labeled dataset.",
        "available_now": ["/metrics/recent", "/models/compare"],
    }


@router.websocket("/detect/webcam")
async def ws_webcam(ws: WebSocket, token: str | None = None):
    """
    Browser sends JSON:
      { "model": "yolo|ssd|fasterrcnn", "score_thresh": 0.25, "frame_b64": "data:image/jpeg;base64,..." }
    Server responds JSON:
      { "processing_ms": 12, "detections": [...], "annotated_jpeg_b64": "data:image/jpeg;base64,..." }
    """
    # WS can't easily use OAuth2 headers from browsers; accept token via query param.
    if token:
        from app.core.security import decode_token
        from sqlmodel import select
        from app.db.session import engine
        from app.db.models import User
        with Session(engine) as session:
            sub = decode_token(token)
            if not sub:
                await ws.close(code=4401)
                return
            user = session.exec(select(User).where(User.email == sub)).first()
            if not user:
                await ws.close(code=4401)
                return

    await ws.accept()
    try:
        while True:
            payload = await ws.receive_json()
            model: ModelName = payload.get("model", "yolo")
            score_thresh = float(payload.get("score_thresh", 0.25))
            frame_b64 = payload["frame_b64"]
            frame_bytes = decode_base64_jpeg(frame_b64)

            dets, processing_ms, device = detect_image_bytes(model, frame_bytes, score_thresh=score_thresh)
            img_bgr = bytes_to_bgr(frame_bytes)
            ann = draw_detections_bgr(img_bgr, dets)
            ann_bytes = bgr_to_jpeg_bytes(ann, quality=75)
            ann_b64 = "data:image/jpeg;base64," + base64.b64encode(ann_bytes).decode("ascii")

            await ws.send_json(
                {
                    "model": model,
                    "device": device,
                    "processing_ms": processing_ms,
                    "detections": [
                        {"label": d.label, "score": d.score, "box": {"x1": d.x1, "y1": d.y1, "x2": d.x2, "y2": d.y2}}
                        for d in dets
                    ],
                    "annotated_jpeg_b64": ann_b64,
                }
            )
    except WebSocketDisconnect:
        return

