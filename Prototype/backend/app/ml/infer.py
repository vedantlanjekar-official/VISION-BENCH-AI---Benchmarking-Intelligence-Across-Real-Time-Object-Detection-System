from __future__ import annotations

import base64
import hashlib
import time
from dataclasses import dataclass
from typing import List, Tuple

import cv2
import numpy as np
import torch
from PIL import Image

from app.ml.model_registry import ModelName, get_loaded_models


@dataclass
class Det:
    label: str
    score: float
    x1: float
    y1: float
    x2: float
    y2: float


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def decode_base64_jpeg(data_url_or_b64: str) -> bytes:
    # Accept "data:image/jpeg;base64,...." or raw base64
    if "," in data_url_or_b64 and data_url_or_b64.strip().lower().startswith("data:"):
        data_url_or_b64 = data_url_or_b64.split(",", 1)[1]
    return base64.b64decode(data_url_or_b64)


def bytes_to_bgr(image_bytes: bytes) -> np.ndarray:
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Unable to decode image")
    return img


def bgr_to_pil_rgb(img_bgr: np.ndarray) -> Image.Image:
    rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)


def _torchvision_postprocess(
    outputs, score_thresh: float, coco_labels: List[str]
) -> List[Det]:
    out = outputs[0]
    boxes = out["boxes"].detach().cpu().numpy()
    scores = out["scores"].detach().cpu().numpy()
    labels = out["labels"].detach().cpu().numpy()
    dets: List[Det] = []
    for box, score, lab in zip(boxes, scores, labels):
        if float(score) < score_thresh:
            continue
        x1, y1, x2, y2 = map(float, box.tolist())
        name = coco_labels[int(lab)] if int(lab) < len(coco_labels) else str(int(lab))
        dets.append(Det(label=name, score=float(score), x1=x1, y1=y1, x2=x2, y2=y2))
    return dets


def coco_class_names() -> List[str]:
    # torchvision's built-in COCO names (including background at index 0)
    return [
        "__background__",
        "person",
        "bicycle",
        "car",
        "motorcycle",
        "airplane",
        "bus",
        "train",
        "truck",
        "boat",
        "traffic light",
        "fire hydrant",
        "stop sign",
        "parking meter",
        "bench",
        "bird",
        "cat",
        "dog",
        "horse",
        "sheep",
        "cow",
        "elephant",
        "bear",
        "zebra",
        "giraffe",
        "backpack",
        "umbrella",
        "handbag",
        "tie",
        "suitcase",
        "frisbee",
        "skis",
        "snowboard",
        "sports ball",
        "kite",
        "baseball bat",
        "baseball glove",
        "skateboard",
        "surfboard",
        "tennis racket",
        "bottle",
        "wine glass",
        "cup",
        "fork",
        "knife",
        "spoon",
        "bowl",
        "banana",
        "apple",
        "sandwich",
        "orange",
        "broccoli",
        "carrot",
        "hot dog",
        "pizza",
        "donut",
        "cake",
        "chair",
        "couch",
        "potted plant",
        "bed",
        "dining table",
        "toilet",
        "tv",
        "laptop",
        "mouse",
        "remote",
        "keyboard",
        "cell phone",
        "microwave",
        "oven",
        "toaster",
        "sink",
        "refrigerator",
        "book",
        "clock",
        "vase",
        "scissors",
        "teddy bear",
        "hair drier",
        "toothbrush",
    ]


@torch.inference_mode()
def detect_image_bytes(
    model: ModelName,
    image_bytes: bytes,
    score_thresh: float = 0.25,
) -> Tuple[List[Det], int, str]:
    loaded = get_loaded_models()
    device = loaded.device
    t0 = time.perf_counter()

    img_bgr = bytes_to_bgr(image_bytes)
    h, w = img_bgr.shape[:2]

    dets: List[Det] = []

    if model == "yolo":
        pil = bgr_to_pil_rgb(img_bgr)
        res = loaded.yolo.predict(pil, verbose=False, device=0 if device.type == "cuda" else "cpu")[0]
        names = res.names
        if res.boxes is not None and len(res.boxes) > 0:
            boxes = res.boxes.xyxy.cpu().numpy()
            conf = res.boxes.conf.cpu().numpy()
            cls = res.boxes.cls.cpu().numpy()
            for xyxy, c, cl in zip(boxes, conf, cls):
                if float(c) < score_thresh:
                    continue
                x1, y1, x2, y2 = map(float, xyxy.tolist())
                dets.append(
                    Det(label=str(names.get(int(cl), int(cl))), score=float(c), x1=x1, y1=y1, x2=x2, y2=y2)
                )
    elif model == "ssd":
        pil = bgr_to_pil_rgb(img_bgr)
        x = loaded.preprocess(pil).to(device)
        outputs = loaded.ssd([x])
        dets = _torchvision_postprocess(outputs, score_thresh, coco_class_names())
    elif model == "fasterrcnn":
        pil = bgr_to_pil_rgb(img_bgr)
        x = loaded.preprocess(pil).to(device)
        outputs = loaded.fasterrcnn([x])
        dets = _torchvision_postprocess(outputs, score_thresh, coco_class_names())
    else:
        raise ValueError(f"Unknown model: {model}")

    processing_ms = int((time.perf_counter() - t0) * 1000)
    return dets, processing_ms, device.type


def draw_detections_bgr(img_bgr: np.ndarray, dets: List[Det]) -> np.ndarray:
    out = img_bgr.copy()
    for d in dets:
        p1 = (int(d.x1), int(d.y1))
        p2 = (int(d.x2), int(d.y2))
        cv2.rectangle(out, p1, p2, (0, 255, 0), 2)
        label = f"{d.label} {d.score:.2f}"
        cv2.putText(out, label, (p1[0], max(0, p1[1] - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3)
        cv2.putText(out, label, (p1[0], max(0, p1[1] - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
    return out


def bgr_to_jpeg_bytes(img_bgr: np.ndarray, quality: int = 85) -> bytes:
    ok, buf = cv2.imencode(".jpg", img_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
    if not ok:
        raise ValueError("Unable to encode JPEG")
    return buf.tobytes()

