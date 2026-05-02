"""
Offline COCO evaluation (mAP/IoU/precision/recall/F1) for the supported detectors.

This is intentionally separated from the real-time API path because it requires
ground-truth labels and is typically run as a batch job.

Usage (example):
  python models/eval_coco.py --model yolo --images_dir path/to/val2017 --ann_json path/to/instances_val2017.json

Notes:
  - For torchvision models, we use torchvision COCO label mapping.
  - For YOLOv8, Ultralytics returns COCO class ids by default for COCO weights.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

import torch
from PIL import Image
from torchmetrics.detection.mean_ap import MeanAveragePrecision
from torchvision.transforms import v2 as T

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from backend.app.ml.infer import coco_class_names  # noqa: E402
from backend.app.ml.model_registry import get_loaded_models  # noqa: E402


def load_coco(ann_json: Path) -> Tuple[Dict[int, dict], Dict[int, List[dict]]]:
    data = json.loads(ann_json.read_text(encoding="utf-8"))
    images = {im["id"]: im for im in data["images"]}
    anns_by_image: Dict[int, List[dict]] = {}
    for a in data["annotations"]:
        anns_by_image.setdefault(a["image_id"], []).append(a)
    return images, anns_by_image


def gt_for_image(anns: List[dict]) -> dict:
    boxes = []
    labels = []
    for a in anns:
        # COCO bbox: [x, y, w, h]
        x, y, w, h = a["bbox"]
        boxes.append([x, y, x + w, y + h])
        labels.append(a["category_id"])
    if not boxes:
        return {"boxes": torch.zeros((0, 4)), "labels": torch.zeros((0,), dtype=torch.long)}
    return {"boxes": torch.tensor(boxes, dtype=torch.float32), "labels": torch.tensor(labels, dtype=torch.long)}


def preds_from_yolo(res) -> dict:
    if res.boxes is None or len(res.boxes) == 0:
        return {"boxes": torch.zeros((0, 4)), "scores": torch.zeros((0,)), "labels": torch.zeros((0,), dtype=torch.long)}
    boxes = torch.tensor(res.boxes.xyxy.cpu().numpy(), dtype=torch.float32)
    scores = torch.tensor(res.boxes.conf.cpu().numpy(), dtype=torch.float32)
    labels = torch.tensor(res.boxes.cls.cpu().numpy(), dtype=torch.long)
    return {"boxes": boxes, "scores": scores, "labels": labels}


def preds_from_torchvision(out) -> dict:
    out0 = out[0]
    return {
        "boxes": out0["boxes"].detach().cpu(),
        "scores": out0["scores"].detach().cpu(),
        "labels": out0["labels"].detach().cpu(),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=["yolo", "ssd", "fasterrcnn"], required=True)
    ap.add_argument("--images_dir", type=Path, required=True)
    ap.add_argument("--ann_json", type=Path, required=True)
    ap.add_argument("--limit", type=int, default=500)
    ap.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    args = ap.parse_args()

    loaded = get_loaded_models()
    device = loaded.device
    if args.device == "cpu":
        device = torch.device("cpu")
    if args.device == "cuda":
        device = torch.device("cuda")

    preprocess = T.Compose([T.ToImage(), T.ToDtype(torch.float32, scale=True)])
    metric = MeanAveragePrecision(box_format="xyxy", iou_type="bbox")

    images, anns_by_image = load_coco(args.ann_json)
    coco_names = coco_class_names()

    ids = list(images.keys())[: args.limit]
    t0 = time.perf_counter()
    for i, image_id in enumerate(ids, 1):
        im = images[image_id]
        path = args.images_dir / im["file_name"]
        pil = Image.open(path).convert("RGB")
        x = preprocess(pil).to(device)

        if args.model == "yolo":
            r = loaded.yolo.predict(pil, verbose=False, device=0 if device.type == "cuda" else "cpu")[0]
            preds = preds_from_yolo(r)
        elif args.model == "ssd":
            out = loaded.ssd([x])
            preds = preds_from_torchvision(out)
        else:
            out = loaded.fasterrcnn([x])
            preds = preds_from_torchvision(out)

        gts = gt_for_image(anns_by_image.get(image_id, []))

        metric.update([preds], [gts])
        if i % 50 == 0:
            print(f"Processed {i}/{len(ids)}")

    res = metric.compute()
    elapsed = time.perf_counter() - t0
    print(json.dumps({k: (float(v) if hasattr(v, "item") else v) for k, v in res.items()}, indent=2))
    print(f"Elapsed: {elapsed:.1f}s; images: {len(ids)}; IPS: {len(ids)/elapsed:.2f}")
    print("Label map note: COCO category_ids are not contiguous; ensure your annotations use standard COCO ids.")


if __name__ == "__main__":
    main()

