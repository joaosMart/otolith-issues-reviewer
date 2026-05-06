"""Read and write annotations to Google Sheets via gspread."""

from datetime import datetime, timezone
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

HEADER = ["image_id", "annotator", "age", "previous_age", "uncertain", "is_issue", "timestamp", "comments", "unusable", "cruise", "station_nr", "individual_id"]


def connect(service_account_info: dict, sheet_name: str) -> gspread.Worksheet:
    """Connect to the Google Sheet and return the first worksheet."""
    creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open(sheet_name)
    worksheet = spreadsheet.sheet1

    # Ensure header row exists and has all columns
    existing = worksheet.row_values(1)
    if existing != HEADER:
        # Only extend if existing header is a prefix of the new one (don't lose data)
        if HEADER[:len(existing)] == existing:
            worksheet.update("A1", [HEADER])
        elif not existing:
            worksheet.update("A1", [HEADER])

    return worksheet


def _get_all_records(worksheet: gspread.Worksheet) -> list[dict]:
    """Get all records, handling rows with fewer columns than the header."""
    data = worksheet.get_all_values()
    if not data:
        return []
    header = data[0]
    records = []
    for row in data[1:]:
        # Pad short rows with empty strings
        padded = row + [""] * (len(header) - len(row))
        records.append(dict(zip(header, padded)))
    return records


def get_annotator_names(worksheet: gspread.Worksheet) -> list[str]:
    """Return sorted list of unique annotator names from the sheet."""
    records = _get_all_records(worksheet)
    names = sorted({r["annotator"] for r in records if r.get("annotator")})
    return names


def load_annotations(worksheet: gspread.Worksheet, annotator: str) -> dict[str, dict]:
    """Load annotations for a specific annotator. Returns {image_id: row_dict}."""
    records = _get_all_records(worksheet)
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
            "comments": record.get("comments", ""),
            "unusable": str(record.get("unusable", "")).upper() == "TRUE",
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
    comments: str = "",
    unusable: bool = False,
    existing_row: int | None = None,
    cruise: str = "",
    station_nr: str = "",
    individual_id: str = "",
):
    """Write or update an annotation row in the sheet."""
    timestamp = datetime.now(timezone.utc).isoformat()
    row_data = [image_id, annotator, age, previous_age, str(uncertain).upper(), str(is_issue).upper(), timestamp, comments, str(unusable).upper(), cruise, station_nr, individual_id]

    if existing_row:
        # Update existing row
        worksheet.update(f"A{existing_row}:L{existing_row}", [row_data])
    else:
        # Append new row
        worksheet.append_row(row_data, value_input_option="RAW")
