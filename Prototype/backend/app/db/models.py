from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    password_hash: str
    role: str = Field(default="user", index=True)  # user|admin
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class MediaAsset(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    kind: str  # image|video|webcam_frame
    filename: str
    content_type: str
    size_bytes: int
    sha256: str
    storage: str = Field(default="local")  # local|s3
    object_key: Optional[str] = None  # for S3 (bucket key) or future stores
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)


class DetectionRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    asset_id: Optional[int] = Field(default=None, foreign_key="mediaasset.id", index=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    model_name: str  # yolo|ssd|fasterrcnn
    device: str  # cpu|cuda
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    processing_ms: int
    fps: Optional[float] = None  # for video/webcam
    artifact_path: Optional[str] = None  # local path (if local)
    artifact_storage: str = Field(default="local")  # local|s3
    artifact_object_key: Optional[str] = None  # S3 key


class Detection(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="detectionrun.id", index=True)
    label: str
    score: float
    x1: float
    y1: float
    x2: float
    y2: float


class MetricsSnapshot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    model_name: str
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    map50: Optional[float] = None
    iou: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1: Optional[float] = None
    fps: Optional[float] = None


class Job(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    kind: str  # video
    status: str = Field(default="queued", index=True)  # queued|running|succeeded|failed
    model_name: str
    score_thresh: float
    asset_id: Optional[int] = Field(default=None, foreign_key="mediaasset.id", index=True)
    run_id: Optional[int] = Field(default=None, foreign_key="detectionrun.id", index=True)
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class RefreshToken(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    token_hash: str = Field(index=True, unique=True)
    revoked_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    expires_at: datetime = Field(index=True)


class AuditLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    actor_user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    action: str = Field(index=True)  # e.g. user.role_change
    target_type: str = Field(index=True)  # e.g. user
    target_id: Optional[int] = Field(default=None, index=True)
    ip: Optional[str] = Field(default=None, index=True)
    user_agent: Optional[str] = None
    fingerprint: Optional[str] = Field(default=None, index=True)
    before: Optional[str] = None  # JSON string
    after: Optional[str] = None  # JSON string
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

