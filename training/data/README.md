# Dataset templates for training

## 1) Detector dataset (YOLO)

Create the following folders:

training/data/detector/
  images/train/
  images/val/
  labels/train/
  labels/val/
  data.yaml

`data.yaml` example:

path: training/data/detector
train: images/train
val: images/val
names:
  0: plate

Each label `.txt` line format:

<class_id> <x_center> <y_center> <width> <height>

All values are normalized to [0, 1].

## 2) OCR dataset (TrOCR)

training/data/ocr/
  images/train/
  images/val/
  labels_train.csv
  labels_val.csv

CSV format:

file,text
img_0001.jpg,1234УБЗ
img_0002.jpg,5678ХОХ

Text must follow NNNNTTT format (4 digits + 3 letters).
