from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Literal, Optional

import torch
from ultralytics import YOLO
from torchvision.models.detection import (
    fasterrcnn_resnet50_fpn_v2,
    ssd300_vgg16,
)
from torchvision.models.detection.faster_rcnn import FasterRCNN
from torchvision.models.detection.ssd import SSD
from torchvision.transforms import v2 as T

from app.core.config import get_settings

ModelName = Literal["yolo", "ssd", "fasterrcnn"]


@dataclass
class LoadedModels:
    device: torch.device
    yolo: Optional[YOLO] = None
    ssd: Optional[SSD] = None
    fasterrcnn: Optional[FasterRCNN] = None
    preprocess: Optional[T.Compose] = None


_loaded: Optional[LoadedModels] = None


def _pick_device() -> torch.device:
    settings = get_settings()
    if settings.model_device == "cpu":
        return torch.device("cpu")
    if settings.model_device == "cuda":
        return torch.device("cuda")
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def get_loaded_models() -> LoadedModels:
    global _loaded
    if _loaded is not None:
        return _loaded

    device = _pick_device()
    settings = get_settings()

    preprocess = T.Compose(
        [
            T.ToImage(),
            T.ToDtype(torch.float32, scale=True),
        ]
    )

    # Torchvision models output COCO class indices. YOLO returns class ids + names.
    ssd = ssd300_vgg16(weights="DEFAULT").to(device).eval()
    faster = fasterrcnn_resnet50_fpn_v2(weights="DEFAULT").to(device).eval()

    yolo = YOLO(settings.yolo_model)  # auto-download if missing

    _loaded = LoadedModels(device=device, yolo=yolo, ssd=ssd, fasterrcnn=faster, preprocess=preprocess)
    return _loaded


def supported_models() -> Dict[str, str]:
    return {
        "yolo": "YOLOv8 (Ultralytics) - default COCO pretrained",
        "ssd": "SSD300 VGG16 (torchvision) - COCO pretrained",
        "fasterrcnn": "Faster R-CNN ResNet50 FPN v2 (torchvision) - COCO pretrained",
    }

