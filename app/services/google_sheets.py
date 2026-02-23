"""Google Sheets service – create, read, write, append rows."""

from typing import Optional

from googleapiclient.discovery import build

from app.services.google_auth import get_credentials


def _get_service():
    creds = get_credentials()
    if not creds:
        raise PermissionError("Google hesabı bağlı değil.")
    return build("sheets", "v4", credentials=creds)


def _get_drive_service():
    creds = get_credentials()
    if not creds:
        raise PermissionError("Google hesabı bağlı değil.")
    return build("drive", "v3", credentials=creds)


def create_spreadsheet(title: str, headers: Optional[list[str]] = None) -> dict:
    """Create a new Google Spreadsheet, optionally with header row."""
    service = _get_service()
    body = {"properties": {"title": title}}
    sheet = service.spreadsheets().create(body=body, fields="spreadsheetId").execute()
    sheet_id = sheet["spreadsheetId"]

    if headers:
        write_range(sheet_id, "A1", [headers])

    return {
        "spreadsheetId": sheet_id,
        "title": title,
        "link": f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit",
    }


def read_range(spreadsheet_id: str, range_name: str = "A1:Z1000") -> dict:
    """Read values from a spreadsheet range."""
    service = _get_service()
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=range_name)
        .execute()
    )
    return {
        "spreadsheetId": spreadsheet_id,
        "range": result.get("range", range_name),
        "values": result.get("values", []),
    }


def write_range(spreadsheet_id: str, range_name: str, values: list[list]) -> dict:
    """Write values to a spreadsheet range."""
    service = _get_service()
    body = {"values": values}
    result = (
        service.spreadsheets()
        .values()
        .update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="USER_ENTERED",
            body=body,
        )
        .execute()
    )
    return {
        "status": "success",
        "updatedCells": result.get("updatedCells", 0),
        "spreadsheetId": spreadsheet_id,
    }


def append_rows(spreadsheet_id: str, values: list[list], range_name: str = "A1") -> dict:
    """Append rows to a spreadsheet."""
    service = _get_service()
    body = {"values": values}
    result = (
        service.spreadsheets()
        .values()
        .append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body=body,
        )
        .execute()
    )
    return {
        "status": "success",
        "updates": result.get("updates", {}),
        "spreadsheetId": spreadsheet_id,
    }


def get_sheet_info(spreadsheet_id: str) -> dict:
    """Get spreadsheet metadata (title, sheets, etc.)."""
    service = _get_service()
    meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets = [
        {"title": s["properties"]["title"], "index": s["properties"]["index"]}
        for s in meta.get("sheets", [])
    ]
    return {
        "spreadsheetId": spreadsheet_id,
        "title": meta["properties"]["title"],
        "sheets": sheets,
        "link": f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit",
    }
