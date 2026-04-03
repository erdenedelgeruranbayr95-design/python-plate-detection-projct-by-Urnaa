"""
Fine-tune TrOCR for license plate text recognition (NNNNTTT format).

Expected OCR dataset layout:
  training/data/ocr/
    images/
      train/*.jpg
      val/*.jpg
    labels_train.csv
    labels_val.csv

CSV format (header required):
  file,text
  img_0001.jpg,1234УБЗ
  img_0002.jpg,5678ХОХ
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import pandas as pd
import torch
from PIL import Image
from datasets import Dataset
from transformers import (
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    TrOCRProcessor,
    VisionEncoderDecoderModel,
)


def load_split(images_dir: Path, labels_csv: Path) -> Dataset:
    if not labels_csv.exists():
        raise FileNotFoundError(f"Labels not found: {labels_csv}")

    df = pd.read_csv(labels_csv)
    required_cols = {"file", "text"}
    if not required_cols.issubset(set(df.columns)):
        raise ValueError(f"{labels_csv} must contain columns: file,text")

    records: List[Dict[str, str]] = []
    for _, row in df.iterrows():
        image_path = images_dir / str(row["file"])
        if image_path.exists() and isinstance(row["text"], str) and row["text"].strip():
            records.append({"image_path": str(image_path), "text": row["text"].strip().upper()})

    if not records:
        raise ValueError(f"No valid records in {labels_csv}")

    return Dataset.from_list(records)


@dataclass
class OCRCollator:
    processor: TrOCRProcessor
    max_target_length: int = 16

    def __call__(self, batch: List[Dict[str, str]]) -> Dict[str, torch.Tensor]:
        images = [Image.open(item["image_path"]).convert("RGB") for item in batch]
        pixel_values = self.processor(images=images, return_tensors="pt").pixel_values

        labels = self.processor.tokenizer(
            [item["text"] for item in batch],
            padding="max_length",
            max_length=self.max_target_length,
            truncation=True,
            return_tensors="pt",
        ).input_ids
        labels[labels == self.processor.tokenizer.pad_token_id] = -100

        return {"pixel_values": pixel_values, "labels": labels}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fine-tune TrOCR on Mongolian plate text")
    parser.add_argument("--data-dir", type=Path, default=Path("training/data/ocr"))
    parser.add_argument("--base-model", type=str, default="microsoft/trocr-small-printed")
    parser.add_argument("--output-dir", type=Path, default=Path("training/runs/ocr_trocr"))
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--train-batch-size", type=int, default=8)
    parser.add_argument("--eval-batch-size", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=5e-5)
    parser.add_argument("--warmup-ratio", type=float, default=0.1)
    parser.add_argument("--max-target-length", type=int, default=16)
    parser.add_argument("--fp16", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    train_ds = load_split(args.data_dir / "images" / "train", args.data_dir / "labels_train.csv")
    val_ds = load_split(args.data_dir / "images" / "val", args.data_dir / "labels_val.csv")

    processor = TrOCRProcessor.from_pretrained(args.base_model)
    model = VisionEncoderDecoderModel.from_pretrained(args.base_model)

    model.config.decoder_start_token_id = processor.tokenizer.cls_token_id
    model.config.pad_token_id = processor.tokenizer.pad_token_id
    model.config.eos_token_id = processor.tokenizer.sep_token_id
    model.config.max_length = args.max_target_length
    model.config.early_stopping = True
    model.config.no_repeat_ngram_size = 0
    model.config.length_penalty = 1.0
    model.config.num_beams = 1

    collator = OCRCollator(processor=processor, max_target_length=args.max_target_length)

    training_args = Seq2SeqTrainingArguments(
        output_dir=str(args.output_dir),
        predict_with_generate=True,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        logging_strategy="steps",
        logging_steps=50,
        learning_rate=args.learning_rate,
        per_device_train_batch_size=args.train_batch_size,
        per_device_eval_batch_size=args.eval_batch_size,
        num_train_epochs=args.epochs,
        warmup_ratio=args.warmup_ratio,
        save_total_limit=3,
        load_best_model_at_end=True,
        fp16=args.fp16,
        dataloader_num_workers=2,
        report_to="none",
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        data_collator=collator,
        tokenizer=processor.feature_extractor,
    )

    trainer.train()
    trainer.save_model(str(args.output_dir / "best"))
    processor.save_pretrained(str(args.output_dir / "best"))

    print(f"[INFO] OCR fine-tuning complete. Saved: {args.output_dir / 'best'}")


if __name__ == "__main__":
    main()
