# Local Training Setup (YOLO + OCR Fine-tune)

This project now includes local training scripts for:
1. Plate detection with YOLOv8
2. Plate text recognition with TrOCR fine-tuning

## Install training dependencies

```bash
pip install -r training/requirements-train.txt
```

## A) Train plate detector (YOLOv8)

1. Prepare dataset in YOLO format (see `training/data/README.md`).
2. Run training:

```bash
python training/train_yolo_detector.py \
  --data training/data/detector/data.yaml \
  --model yolov8n.pt \
  --epochs 100 \
  --imgsz 960 \
  --batch 16 \
  --device 0
```

3. Best model will be saved to:

`training/runs/detector/yolov8_plate/weights/best.pt`

## B) Fine-tune OCR (TrOCR)

1. Prepare OCR dataset (see `training/data/README.md`).
2. Run training:

```bash
python training/train_ocr_trocr.py \
  --data-dir training/data/ocr \
  --base-model microsoft/trocr-small-printed \
  --output-dir training/runs/ocr_trocr \
  --epochs 12 \
  --train-batch-size 8 \
  --eval-batch-size 8 \
  --learning-rate 5e-5 \
  --fp16
```

3. Best model will be saved to:

`training/runs/ocr_trocr/best`

## Notes

- OCR labels must match plate format `NNNNTTT` (example: `1234УБЗ`).
- If GPU memory is low, reduce batch size.
- For CPU-only training, remove `--fp16` and use smaller batch sizes.
