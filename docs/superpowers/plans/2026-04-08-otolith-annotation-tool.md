# Otolith Annotation Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Streamlit app that lets a scientist review ~1400 otolith images and record age estimates to Google Sheets, with HuggingFace-hosted images, metadata display, and resume capability.

**Architecture:** Single-file Streamlit app (`app.py`) backed by three modules: `hf_data.py` (fetch images + CSV from HuggingFace), `sheets.py` (Google Sheets read/write), and `image_utils.py` (brightness/contrast). A separate `upload_to_hf.py` script handles one-time data upload.

**Tech Stack:** Streamlit, huggingface_hub, gspread, google-auth, folium, streamlit-folium, Pillow

---

## File Structure

```
otolith-review-tool/
  app.py                  # Main Streamlit app — UI layout, navigation, session state
  hf_data.py              # Load metadata CSV and fetch images from HuggingFace
  sheets.py               # Google Sheets read/write via gspread
  image_utils.py          # Brightness/contrast adjustment via Pillow
  upload_to_hf.py         # One-time script: upload images + CSV to HuggingFace
  requirements.txt        # Python dependencies
  .streamlit/
    secrets.toml.example  # Template showing required secrets structure
  README.md               # Setup and deployment instructions
```

---

### Task 1: Project Setup and Dependencies

**Files:**
- Create: `requirements.txt`
- Create: `.streamlit/secrets.toml.example`

- [ ] **Step 1: Create requirements.txt**

```
streamlit>=1.30.0
huggingface_hub>=0.20.0
gspread>=6.0.0
google-auth>=2.25.0
folium>=0.15.0
streamlit-folium>=0.18.0
Pillow>=10.0.0
```

- [ ] **Step 2: Create secrets template**

Create `.streamlit/secrets.toml.example`:

```toml
# HuggingFace
HF_TOKEN = "hf_your_token_here"
HF_REPO_ID = "your-username/otolith-dataset"

# Google Sheets
SHEET_NAME = "Otolith Annotations"

[gcp_service_account]
type = "service_account"
project_id = ""
private_key_id = ""
private_key = ""
client_email = ""
client_id = ""
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = ""
```

- [ ] **Step 3: Create .gitignore**

```
__pycache__/
*.pyc
.streamlit/secrets.toml
.superpowers/
```

- [ ] **Step 4: Install dependencies locally**

Run: `pip install -r requirements.txt`
Expected: All packages install successfully.

- [ ] **Step 5: Commit**

```bash
git init
git add requirements.txt .streamlit/secrets.toml.example .gitignore
git commit -m "chore: project setup with dependencies and secrets template"
```

---

### Task 2: HuggingFace Upload Script

**Files:**
- Create: `upload_to_hf.py`

- [ ] **Step 1: Write the upload script**

```python
"""One-time script to upload otolith images and metadata CSV to a HuggingFace dataset repo."""

import argparse
from pathlib import Path
from huggingface_hub import HfApi


def upload_dataset(image_dir: str, metadata_csv: str, repo_id: str, token: str):
    api = HfApi(token=token)

    # Create the repo if it doesn't exist
    api.create_repo(repo_id=repo_id, repo_type="dataset", exist_ok=True)

    # Upload metadata CSV
    csv_path = Path(metadata_csv)
    print(f"Uploading {csv_path.name}...")
    api.upload_file(
        path_or_fileobj=str(csv_path),
        path_in_repo="metadata.csv",
        repo_id=repo_id,
        repo_type="dataset",
    )

    # Upload all JPG images in a folder
    img_dir = Path(image_dir)
    images = sorted(img_dir.glob("*.jpg")) + sorted(img_dir.glob("*.JPG"))
    print(f"Found {len(images)} images to upload.")

    for i, img_path in enumerate(images, 1):
        print(f"  [{i}/{len(images)}] {img_path.name}")
        api.upload_file(
            path_or_fileobj=str(img_path),
            path_in_repo=f"images/{img_path.name}",
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
```

- [ ] **Step 2: Test the script runs without errors (dry check)**

Run: `python upload_to_hf.py --help`
Expected: Shows argument help text without errors.

- [ ] **Step 3: Commit**

```bash
git add upload_to_hf.py
git commit -m "feat: add HuggingFace dataset upload script"
```

---

### Task 3: HuggingFace Data Module

**Files:**
- Create: `hf_data.py`

- [ ] **Step 1: Write hf_data.py**

```python
"""Fetch metadata CSV and images from a HuggingFace dataset repo."""

import io
import csv
from PIL import Image
from huggingface_hub import hf_hub_download


def load_metadata(repo_id: str, token: str) -> list[dict]:
    """Download metadata.csv from HF and return as list of dicts."""
    path = hf_hub_download(
        repo_id=repo_id,
        filename="metadata.csv",
        repo_type="dataset",
        token=token,
    )
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def load_image(repo_id: str, token: str, image_filename: str) -> Image.Image:
    """Download a single image from HF and return as PIL Image."""
    path = hf_hub_download(
        repo_id=repo_id,
        filename=f"images/{image_filename}",
        repo_type="dataset",
        token=token,
    )
    return Image.open(path)
```

- [ ] **Step 2: Commit**

```bash
git add hf_data.py
git commit -m "feat: add HuggingFace data loading module"
```

---

### Task 4: Google Sheets Module

**Files:**
- Create: `sheets.py`

- [ ] **Step 1: Write sheets.py**

```python
"""Read and write annotations to Google Sheets via gspread."""

from datetime import datetime, timezone
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

HEADER = ["image_id", "annotator", "age", "previous_age", "uncertain", "timestamp"]


def connect(service_account_info: dict, sheet_name: str) -> gspread.Worksheet:
    """Connect to the Google Sheet and return the first worksheet."""
    creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open(sheet_name)
    worksheet = spreadsheet.sheet1

    # Ensure header row exists
    existing = worksheet.row_values(1)
    if existing != HEADER:
        worksheet.update("A1", [HEADER])

    return worksheet


def load_annotations(worksheet: gspread.Worksheet) -> dict[str, dict]:
    """Load all annotations from the sheet. Returns {image_id: row_dict}."""
    records = worksheet.get_all_records()
    annotations = {}
    for i, record in enumerate(records):
        annotations[record["image_id"]] = {
            "row_number": i + 2,  # 1-indexed, row 1 is header
            "annotator": record["annotator"],
            "age": int(record["age"]),
            "previous_age": record["previous_age"],
            "uncertain": str(record["uncertain"]).upper() == "TRUE",
            "timestamp": record["timestamp"],
        }
    return annotations


def save_annotation(
    worksheet: gspread.Worksheet,
    image_id: str,
    annotator: str,
    age: int,
    previous_age: int,
    uncertain: bool,
    existing_row: int | None = None,
):
    """Write or update an annotation row in the sheet."""
    timestamp = datetime.now(timezone.utc).isoformat()
    row_data = [image_id, annotator, age, previous_age, str(uncertain).upper(), timestamp]

    if existing_row:
        # Update existing row
        worksheet.update(f"A{existing_row}:F{existing_row}", [row_data])
    else:
        # Append new row
        worksheet.append_row(row_data, value_input_option="RAW")
```

- [ ] **Step 2: Commit**

```bash
git add sheets.py
git commit -m "feat: add Google Sheets annotation module"
```

---

### Task 5: Image Utilities Module

**Files:**
- Create: `image_utils.py`

- [ ] **Step 1: Write image_utils.py**

```python
"""Brightness and contrast adjustments for otolith images using Pillow."""

from PIL import Image, ImageEnhance


def adjust_image(image: Image.Image, brightness: float, contrast: float) -> Image.Image:
    """Apply brightness and contrast adjustments.

    Args:
        image: Source PIL Image.
        brightness: -50 to +50 (0 = no change). Mapped to Pillow factor 0.5–1.5.
        contrast: -50 to +50 (0 = no change). Mapped to Pillow factor 0.5–1.5.

    Returns:
        Adjusted PIL Image.
    """
    # Map slider range (-50 to +50) to Pillow factor (0.5 to 1.5)
    b_factor = 1.0 + (brightness / 100.0)
    c_factor = 1.0 + (contrast / 100.0)

    result = ImageEnhance.Brightness(image).enhance(b_factor)
    result = ImageEnhance.Contrast(result).enhance(c_factor)
    return result
```

- [ ] **Step 2: Commit**

```bash
git add image_utils.py
git commit -m "feat: add image brightness/contrast utility"
```

---

### Task 6: Main Streamlit App — Core Layout and Navigation

**Files:**
- Create: `app.py`

- [ ] **Step 1: Write app.py with full UI**

```python
"""Otolith Annotation Tool — Streamlit app."""

import streamlit as st
import folium
from streamlit_folium import st_folium

from hf_data import load_metadata, load_image
from sheets import connect, load_annotations, save_annotation
from image_utils import adjust_image

# --- Page config ---
st.set_page_config(page_title="Otolith Annotation Tool", layout="wide")

# --- Secrets ---
HF_TOKEN = st.secrets["HF_TOKEN"]
HF_REPO_ID = st.secrets["HF_REPO_ID"]
SHEET_NAME = st.secrets["SHEET_NAME"]
GCP_INFO = dict(st.secrets["gcp_service_account"])


# --- Cached data loading ---
@st.cache_data(ttl=300)
def get_metadata():
    return load_metadata(HF_REPO_ID, HF_TOKEN)


@st.cache_resource
def get_worksheet():
    return connect(GCP_INFO, SHEET_NAME)


# --- Init session state ---
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
    st.session_state.selected_age = None
    st.session_state.uncertain = False

metadata = get_metadata()
worksheet = get_worksheet()
total_images = len(metadata)


# --- Load annotations and find resume point ---
def refresh_annotations():
    return load_annotations(worksheet)


if "annotations" not in st.session_state:
    st.session_state.annotations = refresh_annotations()
    # Jump to first unannotated image
    for i, row in enumerate(metadata):
        if row["image_id"] not in st.session_state.annotations:
            st.session_state.current_index = i
            break


# --- Navigation functions ---
def go_prev():
    if st.session_state.current_index > 0:
        st.session_state.current_index -= 1
        _load_existing_annotation()


def go_next():
    if st.session_state.current_index < total_images - 1:
        st.session_state.current_index += 1
        _load_existing_annotation()


def _load_existing_annotation():
    """Pre-fill age/uncertain if this image was already annotated."""
    current = metadata[st.session_state.current_index]
    ann = st.session_state.annotations.get(current["image_id"])
    if ann:
        st.session_state.selected_age = ann["age"]
        st.session_state.uncertain = ann["uncertain"]
    else:
        st.session_state.selected_age = None
        st.session_state.uncertain = False


# --- Keyboard navigation (arrow keys) ---
# Inject JavaScript to capture arrow key presses
st.components.v1.html(
    """
    <script>
    const doc = window.parent.document;
    doc.addEventListener('keydown', function(e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        if (e.key === 'ArrowLeft') {
            const prevBtn = doc.querySelector('[data-testid="stButton"] button[kind="secondary"]');
            // Find button with "Prev" text
            const buttons = doc.querySelectorAll('[data-testid="stButton"] button');
            buttons.forEach(btn => {
                if (btn.innerText.includes('Prev')) btn.click();
            });
        } else if (e.key === 'ArrowRight') {
            const buttons = doc.querySelectorAll('[data-testid="stButton"] button');
            buttons.forEach(btn => {
                if (btn.innerText.includes('Next')) btn.click();
            });
        }
    });
    </script>
    """,
    height=0,
)


# --- Annotator name ---
annotator = st.sidebar.text_input("Your name", key="annotator_name")

if not annotator:
    st.warning("Please enter your name in the sidebar to begin annotating.")
    st.stop()


# --- Current image data ---
current = metadata[st.session_state.current_index]
image_id = current["image_id"]
existing_ann = st.session_state.annotations.get(image_id)

# Pre-fill if revisiting
if existing_ann and st.session_state.selected_age is None:
    st.session_state.selected_age = existing_ann["age"]
    st.session_state.uncertain = existing_ann["uncertain"]


# --- Layout ---
left_col, right_col = st.columns([65, 35])

# --- Left: Image ---
with left_col:
    # Navigation bar
    nav_cols = st.columns([1, 3, 1])
    with nav_cols[0]:
        st.button("← Prev", on_click=go_prev, disabled=st.session_state.current_index == 0)
    with nav_cols[1]:
        status = "✓" if existing_ann else ""
        st.markdown(
            f"<h3 style='text-align:center;margin:0;'>Image {st.session_state.current_index + 1} / {total_images} {status}</h3>",
            unsafe_allow_html=True,
        )
    with nav_cols[2]:
        st.button("Next →", on_click=go_next, disabled=st.session_state.current_index == total_images - 1)

    # Load and display image
    raw_image = load_image(HF_REPO_ID, HF_TOKEN, image_id)

    brightness = st.slider("Brightness", -50, 50, 0, key="brightness")
    contrast = st.slider("Contrast", -50, 50, 0, key="contrast")

    if brightness != 0 or contrast != 0:
        display_image = adjust_image(raw_image, brightness, contrast)
    else:
        display_image = raw_image

    if st.button("Reset image"):
        st.session_state.brightness = 0
        st.session_state.contrast = 0
        st.rerun()

    st.image(display_image, use_container_width=True)

# --- Right: Controls ---
with right_col:
    # Metadata
    st.subheader("Metadata")
    st.write(f"**Length:** {current.get('length', 'N/A')}")
    st.write(f"**Month:** {current.get('month', 'N/A')}")

    # Map
    lat = current.get("latitude")
    lon = current.get("longitude")
    if lat and lon:
        lat, lon = float(lat), float(lon)
        m = folium.Map(location=[lat, lon], zoom_start=6, width=300, height=200)
        folium.Marker([lat, lon]).add_to(m)
        st_folium(m, width=300, height=200)

    # Age buttons
    st.subheader("Age")
    age_cols = st.columns(5)
    for i in range(1, 21):
        col = age_cols[(i - 1) % 5]
        with col:
            is_selected = st.session_state.selected_age == i
            label = f"**[{i}]**" if is_selected else str(i)
            if st.button(label, key=f"age_{i}", use_container_width=True):
                st.session_state.selected_age = i
                st.rerun()

    # Uncertain flag
    uncertain = st.checkbox("Flag as uncertain", value=st.session_state.uncertain, key="uncertain_cb")
    st.session_state.uncertain = uncertain

    # Submit
    can_submit = st.session_state.selected_age is not None
    if st.button("Submit", type="primary", disabled=not can_submit, use_container_width=True):
        save_annotation(
            worksheet=worksheet,
            image_id=image_id,
            annotator=annotator,
            age=st.session_state.selected_age,
            previous_age=int(current.get("previous_age", 0)),
            uncertain=st.session_state.uncertain,
            existing_row=existing_ann["row_number"] if existing_ann else None,
        )
        # Refresh annotations cache
        st.session_state.annotations = refresh_annotations()
        # Auto-advance
        go_next()
        st.rerun()

    # Progress bar
    annotated_count = len(st.session_state.annotations)
    st.progress(annotated_count / total_images)
    st.caption(f"{annotated_count} / {total_images} annotated")
```

- [ ] **Step 2: Run the app locally to verify it starts**

Run: `streamlit run app.py`
Expected: App loads in browser (will show secrets error if no `.streamlit/secrets.toml` configured — that's expected). Verify the page structure renders.

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "feat: main annotation app with full UI, navigation, and sheets integration"
```

---

### Task 7: Local Testing with Real Data

**Files:**
- Create: `.streamlit/secrets.toml` (local only, gitignored)

- [ ] **Step 1: Set up secrets locally**

Create `.streamlit/secrets.toml` with real credentials (this file is gitignored):

```toml
HF_TOKEN = "hf_your_actual_token"
HF_REPO_ID = "your-username/otolith-dataset"
SHEET_NAME = "Otolith Annotations"

[gcp_service_account]
type = "service_account"
project_id = "your-project"
private_key_id = "your-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "your-sa@your-project.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-sa%40your-project.iam.gserviceaccount.com"
```

- [ ] **Step 2: Upload data to HuggingFace (if not already done)**

Run: `python upload_to_hf.py --image-dir /path/to/images --metadata-csv /path/to/metadata.csv --repo-id your-username/otolith-dataset --token hf_your_token`
Expected: All images and CSV uploaded to HuggingFace.

- [ ] **Step 3: Run and test the full app**

Run: `streamlit run app.py`

Test checklist:
- App loads and shows first unannotated image
- Metadata displays (length, month, map)
- Age buttons work and highlight selection
- Brightness/contrast sliders adjust the image
- Reset button restores sliders
- Submit writes to Google Sheet and advances
- Arrow keys navigate between images
- Revisiting an annotated image shows pre-filled age
- Uncertain flag persists correctly
- Progress bar updates

- [ ] **Step 4: Commit any fixes**

```bash
git add -A
git commit -m "fix: adjustments from local testing"
```

---

### Task 8: Deploy to Streamlit Community Cloud

- [ ] **Step 1: Create GitHub repository**

Run:
```bash
git remote add origin https://github.com/YOUR_USERNAME/otolith-review-tool.git
git branch -M main
git push -u origin main
```

- [ ] **Step 2: Deploy on Streamlit Community Cloud**

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Select the GitHub repo, branch `main`, file `app.py`
4. In "Advanced settings" → "Secrets", paste the contents of your local `.streamlit/secrets.toml`
5. Click "Deploy"

- [ ] **Step 3: Test the deployed app**

Open the Streamlit Cloud URL and run through the same test checklist from Task 7 Step 3.

- [ ] **Step 4: Share with colleague for testing**

Send the Streamlit Cloud URL. Verify they can:
- Enter their name
- Navigate images
- Submit annotations
- See their progress saved

---

### Task 9: Create README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write README.md**

```markdown
# Otolith Annotation Tool

Streamlit app for reviewing otolith images and recording age estimates.

## Setup

### Prerequisites

- Python 3.10+
- HuggingFace account and API token
- Google Cloud service account with Sheets API enabled
- A Google Sheet shared with the service account email

### Install

```bash
pip install -r requirements.txt
```

### Configure secrets

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill in your credentials.

### Upload data

```bash
python upload_to_hf.py \
  --image-dir /path/to/images \
  --metadata-csv /path/to/metadata.csv \
  --repo-id your-username/otolith-dataset \
  --token hf_your_token
```

### Run locally

```bash
streamlit run app.py
```

## Deployment

Deployed on Streamlit Community Cloud. Secrets are configured in the Streamlit dashboard under Advanced Settings.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with setup and deployment instructions"
git push
```
