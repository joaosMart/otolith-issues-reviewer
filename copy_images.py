"""Copy otolith images from raw_images into the repo's images/ folder."""

import csv
import shutil
from pathlib import Path

SRC_ROOT = Path("/Users/joaodsm/Desktop/Joao Workspace/PhD Compilation/otolith-cod/otolith_images/segmented_images")
DST_DIR = Path(__file__).parent / "images"
METADATA = Path(__file__).parent / "issues_metadata.csv"

DST_DIR.mkdir(exist_ok=True)

missing = []
copied = 0

with open(METADATA, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

for row in rows:
    measurement_id = row["measurement_id"]
    age = row["age"]
    filename = f"{measurement_id}.jpg"
    dst = DST_DIR / filename

    if dst.exists():
        copied += 1
        continue

    # Try the expected age folder first
    age_int = int(float(age)) if age else None
    candidate = SRC_ROOT / str(age_int) / filename if age_int else None

    if candidate and candidate.exists():
        shutil.copy2(candidate, dst)
        copied += 1
        continue

    # Search all age folders (handles age=10 stored in older folder, etc.)
    found = None
    for folder in sorted(SRC_ROOT.iterdir()):
        if folder.is_dir():
            p = folder / filename
            if p.exists():
                found = p
                break

    if found:
        shutil.copy2(found, dst)
        copied += 1
    else:
        missing.append(measurement_id)

print(f"Copied: {copied} / {len(rows)}")
if missing:
    print(f"Missing ({len(missing)}):")
    for m in missing:
        print(f"  {m}")
