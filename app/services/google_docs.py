"""Google Docs service – create, read, append text."""

from typing import Optional

from googleapiclient.discovery import build

from app.services.google_auth import get_credentials


def _get_service():
    creds = get_credentials()
    if not creds:
        raise PermissionError("Google hesabı bağlı değil.")
    return build("docs", "v1", credentials=creds)


def _get_drive_service():
    creds = get_credentials()
    if not creds:
        raise PermissionError("Google hesabı bağlı değil.")
    return build("drive", "v3", credentials=creds)


def create_document(title: str, body_text: Optional[str] = None) -> dict:
    """Create a new Google Doc, optionally with initial text."""
    service = _get_service()
    doc = service.documents().create(body={"title": title}).execute()
    doc_id = doc["documentId"]

    if body_text:
        append_text(doc_id, body_text)

    return {
        "documentId": doc_id,
        "title": title,
        "link": f"https://docs.google.com/document/d/{doc_id}/edit",
    }


def read_document(document_id: str) -> dict:
    """Read the full content of a Google Doc."""
    service = _get_service()
    doc = service.documents().get(documentId=document_id).execute()

    # Extract plain text from the document body
    content = ""
    for element in doc.get("body", {}).get("content", []):
        if "paragraph" in element:
            for run in element["paragraph"].get("elements", []):
                if "textRun" in run:
                    content += run["textRun"]["content"]

    return {
        "documentId": document_id,
        "title": doc.get("title", ""),
        "content": content,
        "link": f"https://docs.google.com/document/d/{document_id}/edit",
    }


def append_text(document_id: str, text: str) -> dict:
    """Append text to the end of a Google Doc."""
    service = _get_service()
    requests = [
        {
            "insertText": {
                "location": {"index": 1},
                "text": text,
            }
        }
    ]
    service.documents().batchUpdate(
        documentId=document_id, body={"requests": requests}
    ).execute()
    return {"status": "success", "documentId": document_id}


def find_and_replace(document_id: str, find: str, replace: str) -> dict:
    """Find and replace text in a Google Doc."""
    service = _get_service()
    requests = [
        {
            "replaceAllText": {
                "containsText": {"text": find, "matchCase": True},
                "replaceText": replace,
            }
        }
    ]
    result = service.documents().batchUpdate(
        documentId=document_id, body={"requests": requests}
    ).execute()
    return {"status": "success", "replacements": result}
