from __future__ import annotations

import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import cv2

from app.core.config import get_settings
from app.db.models import Job
from app.db.session import engine
from app.ml.infer import bgr_to_jpeg_bytes, detect_image_bytes, draw_detections_bgr
from app.services.storage import StoredObject, get_bytes, put_bytes
from app.services.persistence import create_run, insert_detections
from sqlmodel import Session

from app.tasks.celery_app import celery_app


@celery_app.task(name="video.process")
def process_video_job(job_id: int, *, max_frames: int = 300) -> dict:
    settings = get_settings()
    artifacts_dir = Path(settings.artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    with Session(engine) as session:
        job = session.get(Job, job_id)
        if not job:
            return {"error": "job not found"}
        job.status = "running"
        job.started_at = datetime.utcnow()
        session.add(job)
        session.commit()

        try:
            # Input bytes can come from local file path or S3 object.
            from app.db.models import MediaAsset

            asset = session.get(MediaAsset, job.asset_id) if job.asset_id else None
            if not asset:
                raise RuntimeError("asset missing")
            if asset.storage == "s3":
                if not asset.object_key:
                    raise RuntimeError("missing s3 object key")
                blob = get_bytes(storage="s3", object_key=asset.object_key)
                tmp_in = artifacts_dir / f"job-{job.id}-input.mp4"
                tmp_in.write_bytes(blob)
                input_path = tmp_in
            else:
                input_path = Path(asset.filename)
                if not input_path.exists():
                    raise RuntimeError(f"input video not found: {input_path}")

            cap = cv2.VideoCapture(str(input_path))
            if not cap.isOpened():
                raise RuntimeError("unable to open video")

            fps_in = cap.get(cv2.CAP_PROP_FPS) or 24.0
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 640)
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 480)

            out_path = artifacts_dir / f"job-{job.id}-annotated.mp4"
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            vw = cv2.VideoWriter(str(out_path), fourcc, float(fps_in), (w, h))

            frames = 0
            total_processing_ms = 0
            first_frame_dets = None
            device = "cpu"

            t0 = time.perf_counter()
            while frames < max_frames:
                ok, frame = cap.read()
                if not ok:
                    break
                frames += 1
                jpg = bgr_to_jpeg_bytes(frame, quality=80)
                dets, processing_ms, device = detect_image_bytes(job.model_name, jpg, score_thresh=job.score_thresh)
                total_processing_ms += processing_ms
                if frames == 1:
                    first_frame_dets = dets
                ann = draw_detections_bgr(frame, dets)
                vw.write(ann)

            elapsed = time.perf_counter() - t0
            fps = float(frames / elapsed) if elapsed > 0 else None

            artifact_obj: StoredObject
            if settings.storage_backend == "s3":
                artifact_obj = put_bytes(kind="artifacts", filename=os.path.basename(str(out_path)), data=out_path.read_bytes())
            else:
                artifact_obj = StoredObject(storage="local", object_key=str(out_path))

            run = create_run(
                session,
                asset_id=job.asset_id,
                user_id=job.user_id,
                model_name=job.model_name,
                device=device,
                processing_ms=int(total_processing_ms),
                fps=fps,
                artifact_path=str(out_path) if artifact_obj.storage == "local" else None,
                artifact_storage=artifact_obj.storage,
                artifact_object_key=artifact_obj.object_key if artifact_obj.storage == "s3" else None,
            )
            if first_frame_dets:
                insert_detections(session, run_id=run.id, dets=first_frame_dets)

            job.status = "succeeded"
            job.finished_at = datetime.utcnow()
            job.run_id = run.id
            session.add(job)
            session.commit()

            return {"job_id": job.id, "run_id": run.id, "frames": frames, "fps": fps, "artifact_path": str(out_path)}
        except Exception as e:
            job.status = "failed"
            job.finished_at = datetime.utcnow()
            job.error = str(e)
            session.add(job)
            session.commit()
            return {"job_id": job.id, "error": str(e)}

