# News Event Classifier Training

Train a fine-tuned DistilBERT model on the HuffPost News Category Dataset for news event classification.

## Dataset

Use `News_Category_Dataset_v3.json` (JSONL format with `headline`, `short_description`, `category`).

## Quick Start

```bash
# From project root
python scripts/train_news_classifier.py --dataset "C:\Users\ADMIN\Desktop\swift project\training datasets\News_Category_Dataset_v3.json"
```

## Options

| Flag | Env | Default | Description |
|------|-----|---------|-------------|
| `--dataset` | `NEWS_TRAIN_DATASET` | Desktop path above | Path to JSONL dataset |
| `--output` | `NEWS_TRAIN_OUTPUT` | `models/news_classifier` | Output model directory |
| `--epochs` | `NEWS_TRAIN_EPOCHS` | 3 | Training epochs per subset |
| `--num-subsets` | `NEWS_TRAIN_NUM_SUBSETS` | 1 | Divide dataset into N subsets; train sequentially |
| `--max-samples` | `NEWS_TRAIN_MAX_SAMPLES` | 0 (all) | Max samples for faster runs |
| `--batch-size` | - | 16 | Batch size |
| `--lr` | - | 2e-5 | Learning rate |

## Training with Subsets

Divide the dataset into chunks and train sequentially (useful for large datasets or memory limits):

```bash
# 4 subsets, 1 epoch each
python scripts/train_news_classifier.py --num-subsets 4 --epochs 1

# 4 subsets + limit samples for faster run
python scripts/train_news_classifier.py --num-subsets 4 --max-samples 10000 --epochs 1
```

## Fast Training (Subset)

```bash
python scripts/train_news_classifier.py --max-samples 5000 --epochs 2
```

## Enable Fine-Tuned Model

After training, set in `.env`:

```
CLASSIFIER_FINETUNED_MODEL_PATH=models/news_classifier
```

The classifier will use the fine-tuned model for news-style text, mapping categories (U.S. NEWS, WORLD NEWS, TECH, etc.) to `EVENT_TYPES` via `news_category_mapping.py`.

## Dependencies

Install training deps (optional):

```bash
pip install datasets scikit-learn accelerate
```
