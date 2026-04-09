"""One-time script to upload otolith images and metadata CSV to a HuggingFace dataset repo."""

import argparse
import shutil
import tempfile
from pathlib import Path
from huggingface_hub import HfApi


def upload_dataset(image_dir: str, metadata_csv: str, repo_id: str, token: str):
    api = HfApi(token=token)

    # Create the repo if it doesn't exist
    api.create_repo(repo_id=repo_id, repo_type="dataset", exist_ok=True)

    # Stage files in a temp directory matching the repo layout
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # Copy metadata CSV
        shutil.copy2(metadata_csv, tmp_path / "metadata.csv")

        # Copy images
        img_dest = tmp_path / "images"
        img_dest.mkdir()
        img_dir_path = Path(image_dir)
        images = sorted(img_dir_path.glob("*.jpg")) + sorted(img_dir_path.glob("*.JPG"))
        print(f"Found {len(images)} images to upload.")
        for img in images:
            shutil.copy2(img, img_dest / img.name)

        # Upload with large folder support (handles retries and chunking)
        print("Uploading folder to HuggingFace...")
        api.upload_large_folder(
            folder_path=str(tmp_path),
            repo_id=repo_id,
            repo_type="dataset",
        )

    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload otolith dataset to HuggingFace")
    parser.add_argument("--image-dir", required=True, help="Directory containing JPG images")
    parser.add_argument("--metadata-csv", required=True, help="Path to metadata CSV file")
    parser.add_argument("--repo-id", required=True, help="HuggingFace repo ID (e.g. user/dataset)")
    parser.add_argument("--token", required=True, help="HuggingFace API token")
    args = parser.parse_args()

    upload_dataset(args.image_dir, args.metadata_csv, args.repo_id, args.token)
