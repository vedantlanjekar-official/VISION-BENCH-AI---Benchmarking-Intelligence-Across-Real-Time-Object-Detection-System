from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class Box(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class DetectionItem(BaseModel):
    label: str
    score: float = Field(ge=0.0, le=1.0)
    box: Box


class DetectResponse(BaseModel):
    model: str
    device: str
    processing_ms: int
    detections: List[DetectionItem]
    asset_id: Optional[int] = None
    run_id: Optional[int] = None

