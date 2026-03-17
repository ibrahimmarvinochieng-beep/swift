#!/usr/bin/env python3
"""Train a news event classifier on News_Category_Dataset_v3.json.

CPU-optimized: lazy loading, small batches, gradient checkpointing, low memory.

Usage:
  python scripts/train_news_classifier.py
  python scripts/train_news_classifier.py --dataset "C:/path/to/News_Category_Dataset_v3.json"
  python scripts/train_news_classifier.py --num-subsets 4 --lazy  # Lazy load (recommended for CPU)
  python scripts/train_news_classifier.py --epochs 3 --output models/news_classifier

Environment:
  NEWS_TRAIN_DATASET  - Path to JSONL dataset
  NEWS_TRAIN_OUTPUT   - Output model directory
  NEWS_TRAIN_EPOCHS   - Training epochs per subset
  NEWS_TRAIN_NUM_SUBSETS - Number of subsets (default: 1)
  NEWS_TRAIN_LAZY     - Use lazy loading (default: 1 for CPU)
"""

import argparse
import json
import os
import random
import sys
from pathlib import Path

# Add project root and scripts dir
_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_root))
sys.path.insert(0, str(_root / "scripts"))


def _parse_line(line: str) -> tuple[str, str] | None:
    """Parse JSONL line. Returns (text, category) or None."""
    line = line.strip()
    if line.startswith("Now "):
        line = line[4:].strip()
    if not line:
        return None
    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        return None
    headline = obj.get("headline", "")
    desc = obj.get("short_description", "")
    category = obj.get("category", "").strip()
    if not category or (not headline and not desc):
        return None
    text = f"{headline}. {desc}".strip()[:512]
    if len(text) < 10:
        return None
    return text, category


def stream_index_jsonl(path: str, max_samples: int = 0) -> tuple[list[tuple[int, str]], list[str]]:
    """Single pass: build (byte_offset, category) index. Returns (index, categories)."""
    index: list[tuple[int, str]] = []
    categories: set[str] = set()

    with open(path, "rb") as f:
        offset = 0
        for line in f:
            pos = offset
            offset += len(line)
            try:
                decoded = line.decode("utf-8")
            except UnicodeDecodeError:
                continue
            parsed = _parse_line(decoded)
            if parsed is None:
                continue
            text, category = parsed
            categories.add(category)
            index.append((pos, category))
            if max_samples > 0 and len(index) >= max_samples:
                break

    return index, sorted(categories)


class LazyJsonlDataset:
    """PyTorch Dataset that reads from JSONL on demand. No full load into RAM."""

    def __init__(self, path: str, indices: list[tuple[int, int]], label2id: dict[str, int], tokenizer, max_length: int = 256):
        self.path = path
        self.indices = indices  # (offset, label_id)
        self.label2id = label2id
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.indices)

    def __getitem__(self, idx: int) -> dict:
        offset, label_id = self.indices[idx]
        with open(self.path, "r", encoding="utf-8") as f:
            f.seek(offset)
            line = f.readline()
        parsed = _parse_line(line)
        if parsed is None:
            text = ""
        else:
            text, _ = parsed
        enc = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_length,
            padding="max_length",
            return_tensors=None,
        )
        return {
            "input_ids": enc["input_ids"],
            "attention_mask": enc["attention_mask"],
            "labels": label_id,
        }


def load_dataset(path: str) -> tuple[list[str], list[str], list[str]]:
    """Load JSONL dataset into memory (fallback when not using lazy)."""
    texts = []
    labels = []
    seen_categories = set()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            parsed = _parse_line(line)
            if parsed is None:
                continue
            text, category = parsed
            texts.append(text)
            labels.append(category)
            seen_categories.add(category)
    return texts, labels, sorted(seen_categories)


def main():
    parser = argparse.ArgumentParser(description="Train news event classifier (CPU-optimized)")
    parser.add_argument(
        "--dataset",
        default=os.environ.get(
            "NEWS_TRAIN_DATASET",
            r"C:\Users\ADMIN\Desktop\swift project\training datasets\News_Category_Dataset_v3.json",
        ),
        help="Path to News_Category_Dataset_v3.json",
    )
    parser.add_argument(
        "--output",
        default=os.environ.get("NEWS_TRAIN_OUTPUT", "models/news_classifier"),
        help="Output model directory",
    )
    parser.add_argument("--epochs", type=int, default=int(os.environ.get("NEWS_TRAIN_EPOCHS", "3")))
    parser.add_argument(
        "--max-samples",
        type=int,
        default=int(os.environ.get("NEWS_TRAIN_MAX_SAMPLES", "0")),
        help="Max samples (0 = all)",
    )
    parser.add_argument(
        "--num-subsets",
        type=int,
        default=int(os.environ.get("NEWS_TRAIN_NUM_SUBSETS", "1")),
        help="Divide dataset into N subsets; train sequentially",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=int(os.environ.get("NEWS_TRAIN_BATCH_SIZE", "4")),
        help="Batch size (CPU: use 4 or 8)",
    )
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument(
        "--lazy",
        action="store_true",
        default=os.environ.get("NEWS_TRAIN_LAZY", "1").lower() in ("1", "true", "yes"),
        help="Use lazy loading (read from disk on demand) - recommended for CPU",
    )
    parser.add_argument(
        "--no-lazy",
        action="store_true",
        help="Disable lazy loading, load full dataset into RAM",
    )
    parser.add_argument(
        "--monitor-ram",
        action="store_true",
        default=os.environ.get("NEWS_TRAIN_MONITOR_RAM", "").lower() in ("1", "true", "yes"),
        help="Pause training when RAM usage > 90%% (requires psutil)",
    )
    parser.add_argument(
        "--dataloader-workers",
        type=int,
        default=int(os.environ.get("NEWS_TRAIN_DATALOADER_WORKERS", "0")),
        help="DataLoader workers (0 = main process only, recommended for CPU)",
    )
    args = parser.parse_args()

    if args.no_lazy:
        args.lazy = False

    if not os.path.isfile(args.dataset):
        print(f"Dataset not found: {args.dataset}")
        sys.exit(1)

    from transformers import (
        AutoTokenizer,
        AutoModelForSequenceClassification,
        TrainingArguments,
        Trainer,
        DataCollatorWithPadding,
    )
    from transformers import EvalPrediction
    import numpy as np

    model_name = "distilbert-base-uncased"
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    tokenizer = AutoTokenizer.from_pretrained(model_name)

    if args.lazy:
        print("Building index (streaming, no full load)...")
        index, categories = stream_index_jsonl(args.dataset, args.max_samples or 0)
        print(f"Indexed {len(index)} samples, {len(categories)} categories")

        label2id = {c: i for i, c in enumerate(categories)}
        id2label = {i: c for c, i in label2id.items()}

        # Stratified split on indices
        from collections import defaultdict
        by_cat: dict[str, list[tuple[int, str]]] = defaultdict(list)
        for t in index:
            by_cat[t[1]].append(t)

        all_train, all_val = [], []
        for cat, items in by_cat.items():
            random.Random(42).shuffle(items)
            n_val = max(1, int(len(items) * 0.1))
            val_items = items[:n_val]
            train_items = items[n_val:]
            for pos, _ in val_items:
                all_val.append((pos, label2id[cat]))
            for pos, _ in train_items:
                all_train.append((pos, label2id[cat]))

        random.Random(42).shuffle(all_train)
        random.Random(42).shuffle(all_val)

        num_subsets = max(1, args.num_subsets)
        if num_subsets > 1:
            from sklearn.model_selection import KFold
            kf = KFold(n_splits=num_subsets, shuffle=True, random_state=42)
            subset_indices = list(kf.split(all_train))
        else:
            subset_indices = [(list(range(len(all_train))), [])]

        val_ds = LazyJsonlDataset(args.dataset, all_val, label2id, tokenizer)

    else:
        print("Loading dataset...")
        texts, labels, categories = load_dataset(args.dataset)
        if args.max_samples > 0:
            from collections import defaultdict
            by_cat = defaultdict(list)
            for t, l in zip(texts, labels):
                by_cat[l].append((t, l))
            texts, labels = [], []
            n_per = max(1, args.max_samples // len(categories))
            for cat in categories:
                for t, l in by_cat[cat][:n_per]:
                    texts.append(t)
                    labels.append(l)
            print(f"Subsampled to {len(texts)} samples")

        label2id = {c: i for i, c in enumerate(categories)}
        id2label = {i: c for c, i in label2id.items()}

        from sklearn.model_selection import train_test_split
        X_train_full, X_val, y_train_full, y_val = train_test_split(
            texts, labels, test_size=0.1, stratify=labels, random_state=42
        )

        num_subsets = max(1, args.num_subsets)
        if num_subsets > 1:
            from sklearn.model_selection import StratifiedKFold
            skf = StratifiedKFold(n_splits=num_subsets, shuffle=True, random_state=42)
            subset_indices = list(skf.split(X_train_full, y_train_full))
        else:
            subset_indices = [(list(range(len(X_train_full))), [])]

        from datasets import Dataset

        def tokenize(examples):
            return tokenizer(examples["text"], truncation=True, max_length=256)

        val_ds = Dataset.from_dict({
            "text": X_val,
            "label": [label2id[l] for l in y_val],
        })
        val_ds = val_ds.map(tokenize, batched=True, remove_columns=["text"])

    def compute_metrics(eval_pred: EvalPrediction):
        preds = np.argmax(eval_pred.predictions, axis=1)
        acc = (preds == eval_pred.label_ids).mean()
        return {"accuracy": float(acc)}

    model = None
    for subset_idx, (train_idx, _) in enumerate(subset_indices):
        if args.lazy:
            train_indices = [all_train[i] for i in train_idx]
            train_ds = LazyJsonlDataset(args.dataset, train_indices, label2id, tokenizer)
        else:
            X_train = [X_train_full[i] for i in train_idx]
            y_train = [y_train_full[i] for i in train_idx]
            train_ds = Dataset.from_dict({
                "text": X_train,
                "label": [label2id[l] for l in y_train],
            })
            train_ds = train_ds.map(tokenize, batched=True, remove_columns=["text"])

        print(f"\n--- Subset {subset_idx + 1}/{num_subsets}: {len(train_ds)} samples ---")

        if model is None:
            model = AutoModelForSequenceClassification.from_pretrained(
                model_name,
                num_labels=len(categories),
                id2label=id2label,
                label2id=label2id,
            )
            if hasattr(model, "gradient_checkpointing_enable"):
                model.gradient_checkpointing_enable()
        else:
            model = AutoModelForSequenceClassification.from_pretrained(
                str(output_dir),
                num_labels=len(categories),
                id2label=id2label,
                label2id=label2id,
            )
            if hasattr(model, "gradient_checkpointing_enable"):
                model.gradient_checkpointing_enable()

        subset_out = output_dir / f"subset_{subset_idx}" if num_subsets > 1 else output_dir
        subset_out.mkdir(parents=True, exist_ok=True)

        training_args = TrainingArguments(
            output_dir=str(subset_out),
            num_train_epochs=args.epochs,
            per_device_train_batch_size=args.batch_size,
            per_device_eval_batch_size=min(args.batch_size * 2, 16),
            learning_rate=args.lr,
            warmup_ratio=0.1,
            logging_steps=min(50, max(1, len(train_ds) // args.batch_size)),
            eval_strategy="epoch",
            save_strategy="epoch",
            load_best_model_at_end=True,
            metric_for_best_model="accuracy",
            dataloader_num_workers=args.dataloader_workers,
            dataloader_pin_memory=False,
        )

        callbacks = []
        if args.monitor_ram:
            try:
                from scripts.train_callbacks import MemoryMonitorCallback  # pyright: ignore[reportMissingImports]
                callbacks.append(MemoryMonitorCallback(threshold=0.9))
            except ImportError:
                pass

        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=train_ds,
            eval_dataset=val_ds,
            processing_class=tokenizer,
            data_collator=DataCollatorWithPadding(tokenizer=tokenizer),
            compute_metrics=compute_metrics,
            callbacks=callbacks if callbacks else None,
        )

        trainer.train()
        trainer.save_model(str(output_dir))
        tokenizer.save_pretrained(str(output_dir))

    config = {
        "id2label": id2label,
        "label2id": label2id,
        "categories": categories,
    }
    with open(output_dir / "category_config.json", "w") as f:
        json.dump(config, f, indent=2)

    print(f"\nModel saved to {output_dir}")
    print("Categories:", categories)


if __name__ == "__main__":
    main()
