"""Google Drive service – list, search, download files."""

import io
from typing import Optional

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from app.services.google_auth import get_credentials


def _get_service():
    creds = get_credentials()
    if not creds:
        raise PermissionError("Google hesabı bağlı değil. Lütfen önce giriş yapın.")
    return build("drive", "v3", credentials=creds)


def list_files(query: Optional[str] = None, page_size: int = 20) -> list[dict]:
    """List files from Google Drive, optionally filtered by a query."""
    service = _get_service()
    q = query if query else None
    results = (
        service.files()
        .list(
            pageSize=page_size,
            fields="files(id, name, mimeType, modifiedTime, size, webViewLink)",
            q=q,
            orderBy="modifiedTime desc",
        )
        .execute()
    )
    return results.get("files", [])


def search_files(name: str) -> list[dict]:
    """Search for files by name."""
    query = f"name contains '{name}' and trashed = false"
    return list_files(query=query)


def get_file_metadata(file_id: str) -> dict:
    """Get metadata for a specific file."""
    service = _get_service()
    return (
        service.files()
        .get(fileId=file_id, fields="id, name, mimeType, modifiedTime, size, webViewLink, parents")
        .execute()
    )


def download_file(file_id: str) -> tuple[bytes, str]:
    """Download a file and return (content_bytes, filename)."""
    service = _get_service()
    meta = service.files().get(fileId=file_id, fields="name, mimeType").execute()
    filename = meta["name"]
    mime = meta.get("mimeType", "")

    # Google Workspace files need to be exported
    export_map = {
        "application/vnd.google-apps.document": (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".docx",
        ),
        "application/vnd.google-apps.spreadsheet": (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xlsx",
        ),
        "application/vnd.google-apps.presentation": (
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".pptx",
        ),
    }

    buf = io.BytesIO()
    if mime in export_map:
        export_mime, ext = export_map[mime]
        request = service.files().export_media(fileId=file_id, mimeType=export_mime)
        if not filename.endswith(ext):
            filename += ext
    else:
        request = service.files().get_media(fileId=file_id)

    downloader = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()

    return buf.getvalue(), filename


def create_folder(name: str, parent_id: Optional[str] = None) -> dict:
    """Create a folder in Google Drive."""
    service = _get_service()
    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parent_id:
        metadata["parents"] = [parent_id]
    return service.files().create(body=metadata, fields="id, name, webViewLink").execute()
