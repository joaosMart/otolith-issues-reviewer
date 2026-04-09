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
