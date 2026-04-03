"""
Train a YOLOv8 detector for Mongolian license plate localization.

Expected dataset layout (YOLO format):
  training/data/detector/
    images/train/*.jpg
    images/val/*.jpg
    labels/train/*.txt
    labels/val/*.txt
    data.yaml

Example data.yaml:
  path: training/data/detector
  train: images/train
  val: images/val
  names:
    0: plate
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ultralytics import YOLO


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train YOLOv8 plate detector")
    parser.add_argument("--data", type=Path, default=Path("training/data/detector/data.yaml"), help="Path to YOLO data.yaml")
    parser.add_argument("--model", type=str, default="yolov8n.pt", help="Base YOLO weights")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=960)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--device", type=str, default="0", help="CUDA device id (e.g. 0) or cpu")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--project", type=str, default="training/runs/detector")
    parser.add_argument("--name", type=str, default="yolov8_plate")
    parser.add_argument("--patience", type=int, default=30)
    parser.add_argument("--save-period", type=int, default=10)
    parser.add_argument("--no-amp", action="store_true", help="Disable AMP mixed precision")
    parser.add_argument("--export", action="store_true", help="Export best model to ONNX after training")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.data.exists():
        raise FileNotFoundError(f"data.yaml not found: {args.data}")

    model = YOLO(args.model)
    model.train(
        data=str(args.data),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        workers=args.workers,
        project=args.project,
        name=args.name,
        patience=args.patience,
        save_period=args.save_period,
        amp=not args.no_amp,
        verbose=True,
    )

    # Validate with best checkpoint.
    best_pt = Path(args.project) / args.name / "weights" / "best.pt"
    if best_pt.exists():
        best_model = YOLO(str(best_pt))
        best_model.val(data=str(args.data), imgsz=args.imgsz, device=args.device)
        if args.export:
            best_model.export(format="onnx", simplify=True)
            print("[INFO] Exported ONNX from best.pt")
    else:
        print(f"[WARN] best.pt not found at {best_pt}")


if __name__ == "__main__":
    main()
