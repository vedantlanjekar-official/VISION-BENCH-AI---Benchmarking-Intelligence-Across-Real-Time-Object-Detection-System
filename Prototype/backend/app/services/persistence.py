from __future__ import annotations

from typing import Iterable, Optional

from sqlmodel import Session

from app.db.models import Detection, DetectionRun, MediaAsset
from app.ml.infer import Det


def create_asset(
    session: Session,
    *,
    kind: str,
    filename: str,
    content_type: str,
    size_bytes: int,
    sha256: str,
    storage: str = "local",
    object_key: Optional[str] = None,
) -> MediaAsset:
    asset = MediaAsset(
        kind=kind,
        filename=filename,
        content_type=content_type,
        size_bytes=size_bytes,
        sha256=sha256,
        storage=storage,
        object_key=object_key,
    )
    session.add(asset)
    session.commit()
    session.refresh(asset)
    return asset


def create_run(
    session: Session,
    *,
    asset_id: Optional[int],
    user_id: Optional[int] = None,
    model_name: str,
    device: str,
    processing_ms: int,
    fps: Optional[float] = None,
    artifact_path: Optional[str] = None,
    artifact_storage: str = "local",
    artifact_object_key: Optional[str] = None,
) -> DetectionRun:
    run = DetectionRun(
        asset_id=asset_id,
        user_id=user_id,
        model_name=model_name,
        device=device,
        processing_ms=processing_ms,
        fps=fps,
        artifact_path=artifact_path,
        artifact_storage=artifact_storage,
        artifact_object_key=artifact_object_key,
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def insert_detections(session: Session, *, run_id: int, dets: Iterable[Det]) -> None:
    rows = [
        Detection(
            run_id=run_id,
            label=d.label,
            score=d.score,
            x1=d.x1,
            y1=d.y1,
            x2=d.x2,
            y2=d.y2,
        )
        for d in dets
    ]
    session.add_all(rows)
    session.commit()

