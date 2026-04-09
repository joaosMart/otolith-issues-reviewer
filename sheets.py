"""Read and write annotations to Google Sheets via gspread."""

from datetime import datetime, timezone
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

HEADER = ["image_id", "annotator", "age", "previous_age", "uncertain", "is_issue", "timestamp"]


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


def get_annotator_names(worksheet: gspread.Worksheet) -> list[str]:
    """Return sorted list of unique annotator names from the sheet."""
    records = worksheet.get_all_records()
    names = sorted({r["annotator"] for r in records if r.get("annotator")})
    return names


def load_annotations(worksheet: gspread.Worksheet, annotator: str) -> dict[str, dict]:
    """Load annotations for a specific annotator. Returns {image_id: row_dict}."""
    records = worksheet.get_all_records()
    annotations = {}
    for i, record in enumerate(records):
        if record["annotator"] != annotator:
            continue
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
    is_issue: bool,
    existing_row: int | None = None,
):
    """Write or update an annotation row in the sheet."""
    timestamp = datetime.now(timezone.utc).isoformat()
    row_data = [image_id, annotator, age, previous_age, str(uncertain).upper(), str(is_issue).upper(), timestamp]

    if existing_row:
        # Update existing row
        worksheet.update(f"A{existing_row}:G{existing_row}", [row_data])
    else:
        # Append new row
        worksheet.append_row(row_data, value_input_option="RAW")
