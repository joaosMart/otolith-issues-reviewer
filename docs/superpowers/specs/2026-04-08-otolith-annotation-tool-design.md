# Otolith Annotation Tool — Design Spec

## Overview

A Streamlit web app for a trained scientist to review ~1400 otolith images and assign age estimates (1–20). The app displays each image with metadata, records annotations to Google Sheets in real time, and supports resuming from where the annotator left off.

## Stack

- **Frontend/app:** Streamlit (Python)
- **Image + metadata storage:** HuggingFace dataset repo
- **Annotation storage:** Google Sheets (via gspread)
- **Hosting:** Streamlit Community Cloud

## Architecture & Data Flow

1. **Metadata CSV** lives in a HuggingFace dataset repo. Contains image filenames, length, month, latitude/longitude, and previous age estimate. This is the source of truth for image info.
2. **Images** (JPG) live in the same HuggingFace dataset repo. The app fetches them on demand via `huggingface_hub`.
3. **Google Sheet** is the annotation log — records the annotator's age estimates, flags, and timestamps. One row per annotation.
4. On app load, the app reads the metadata CSV and the Google Sheet, cross-references them to determine which images are annotated and which remain, then jumps to the first unannotated image.

## Google Sheet Schema

| Column | Type | Description |
|--------|------|-------------|
| `image_id` | string | Filename or unique identifier |
| `annotator` | string | Name entered once via a text input at the top of the sidebar (persisted in session state) |
| `age` | int | Annotator's age estimate (1–20) |
| `previous_age` | int | Age from metadata CSV (hidden from annotator during review, stored for later QC) |
| `uncertain` | boolean | Flag indicating low confidence |
| `timestamp` | string | ISO 8601 timestamp of submission |

The `previous_age` is pulled from the metadata CSV at submission time so the sheet is self-contained for analysis.

## UI Layout — Side Panel

### Left Side (~65% width) — Image Area

- Otolith JPG image fetched from HuggingFace, displayed at full column width
- **Brightness slider** below image (-50% to +50%, default 0)
- **Contrast slider** below image (-50% to +50%, default 0)
- **Reset button** to restore sliders to default
- Image adjustments applied via Pillow (`ImageEnhance`) for reliable rendering in Streamlit

### Right Side (~35% width) — Controls

- **Progress counter:** "Image 42 / 1400"
- **Metadata panel:**
  - Length (from CSV)
  - Month (from CSV)
  - Mini map showing catch location (latitude/longitude plotted with `folium` via `streamlit-folium`)
- **Age input:** Grid of buttons numbered 1–20. Selected age is visually highlighted.
- **Uncertain flag:** Checkbox, unchecked by default
- **Submit button:** Writes annotation to Google Sheet and auto-advances to next image

### Navigation

- **Left/right arrow keys** to move between images (keyboard navigation)
- **Prev/Next buttons** as clickable fallback
- On load, jumps to the **first unannotated image**
- Free navigation backward to already-annotated images — their age displays pre-filled and is editable
- Re-submitting an already-annotated image **updates** the existing row in the Google Sheet

### Submission Behavior

1. Annotator selects age (1–20 button) and optionally checks "uncertain"
2. Clicks Submit (or uses a keyboard shortcut)
3. App writes one row to Google Sheet: image_id, annotator, age, previous_age (from CSV, hidden), uncertain, timestamp
4. App auto-advances to the next image
5. If updating an existing annotation, the row is overwritten rather than duplicated

## Bias Prevention

The **previous age** from the metadata CSV is **never shown** to the annotator in the UI. It is only written to the Google Sheet at submission time for downstream QC analysis.

## Dependencies

- `streamlit` — app framework
- `huggingface_hub` — fetch images and metadata CSV from HF dataset repo
- `gspread` + `google-auth` — Google Sheets read/write
- `folium` + `streamlit-folium` — map visualization for catch location
- `Pillow` — image brightness/contrast adjustment

## Deployment

- Code pushed to a GitHub repository
- Streamlit Community Cloud connects to the repo for automatic deployment
- Secrets stored in Streamlit's secrets manager (not in code):
  - **HuggingFace API token** — read access to the dataset repo
  - **Google service account JSON** — write access to the annotation Google Sheet

## Phases

### Phase 1 — Data Prep
- Organize images + metadata CSV locally
- Write upload script to push images and CSV to HuggingFace dataset repo
- Create Google Sheet and configure service account access via gspread

### Phase 2 — App Build
- Image viewer with side-panel layout
- Metadata display with folium map
- Age buttons (1–20) with visual selection
- Brightness/contrast sliders with Pillow
- Google Sheets integration (read on load, write on submit)
- Keyboard arrow navigation (left/right)
- Skip/flag as uncertain with annotation
- Resume from first unannotated image
- Free backward navigation with edit capability

### Phase 3 — Deploy
- Push to GitHub
- Connect to Streamlit Community Cloud
- Configure secrets
- End-to-end testing
