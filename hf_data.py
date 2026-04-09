"""Fetch metadata CSV and images from a HuggingFace dataset repo."""

import csv
import random
from PIL import Image
from huggingface_hub import hf_hub_download


def load_metadata(repo_id: str, token: str) -> list[dict]:
    """Download metadata.csv from HF and return as shuffled list of dicts."""
    path = hf_hub_download(
        repo_id=repo_id,
        filename="metadata.csv",
        repo_type="dataset",
        token=token,
    )
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for r in reader:
            rows.append({
                "image_id": f"{r['measurement_id']}.jpg",
                "measurement_id": r["measurement_id"],
                "previous_age": r.get("age", ""),
                "length": r.get("length", ""),
                "month": r.get("month", ""),
                "latitude": r.get("shot_latitude", ""),
                "longitude": r.get("shot_longitude", ""),
                "is_issue": r.get("is_issue", ""),
            })
    # Shuffle with fixed seed so order is random but consistent
    random.seed(42)
    random.shuffle(rows)
    return rows


def load_image(repo_id: str, token: str, image_filename: str) -> Image.Image:
    """Download a single image from HF and return as PIL Image."""
    path = hf_hub_download(
        repo_id=repo_id,
        filename=f"images/{image_filename}",
        repo_type="dataset",
        token=token,
    )
    return Image.open(path)
