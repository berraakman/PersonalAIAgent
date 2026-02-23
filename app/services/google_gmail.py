"""Gmail service – create drafts, send emails, list messages."""

import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from googleapiclient.discovery import build

from app.services.google_auth import get_credentials


def _get_service():
    creds = get_credentials()
    if not creds:
        raise PermissionError("Google hesabı bağlı değil.")
    return build("gmail", "v1", credentials=creds)


def _build_message(to: str, subject: str, body: str, cc: str = "", bcc: str = "") -> dict:
    """Build a raw email message."""
    message = MIMEMultipart()
    message["to"] = to
    message["subject"] = subject
    if cc:
        message["cc"] = cc
    if bcc:
        message["bcc"] = bcc
    message.attach(MIMEText(body, "html"))
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {"raw": raw}


def send_email(
    to: str,
    subject: str,
    body: str,
    cc: str = "",
    bcc: str = "",
) -> dict:
    """Send an email via Gmail."""
    service = _get_service()
    message = _build_message(to, subject, body, cc, bcc)
    sent = service.users().messages().send(userId="me", body=message).execute()
    return {
        "id": sent["id"],
        "threadId": sent.get("threadId", ""),
        "status": "sent",
    }


def create_draft(
    to: str,
    subject: str,
    body: str,
    cc: str = "",
    bcc: str = "",
) -> dict:
    """Create a Gmail draft."""
    service = _get_service()
    message = _build_message(to, subject, body, cc, bcc)
    draft = service.users().drafts().create(
        userId="me", body={"message": message}
    ).execute()
    return {
        "id": draft["id"],
        "messageId": draft["message"]["id"],
        "status": "draft_created",
    }


def list_messages(query: str = "", max_results: int = 10) -> list[dict]:
    """List Gmail messages, optionally filtered by query."""
    service = _get_service()
    
    # Gelen kutusundan aramak için varsayılan olarak 'in:inbox' ekliyoruz
    if not query:
        query = "in:inbox"
    elif "in:" not in query:
        query = f"in:inbox {query}"

    results = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=max_results)
        .execute()
    )
    messages = []
    for msg_meta in results.get("messages", []):
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=msg_meta["id"], format="metadata",
                 metadataHeaders=["Subject", "From", "Date"])
            .execute()
        )
        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        messages.append({
            "id": msg["id"],
            "threadId": msg.get("threadId", ""),
            "subject": headers.get("Subject", ""),
            "from": headers.get("From", ""),
            "date": headers.get("Date", ""),
            "snippet": msg.get("snippet", ""),
        })
    return messages


def get_message(message_id: str) -> dict:
    """Get full details of a specific message."""
    service = _get_service()
    msg = service.users().messages().get(userId="me", id=message_id, format="full").execute()
    headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}

    # Extract body
    body = ""
    payload = msg.get("payload", {})
    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain":
                data = part["body"].get("data", "")
                body = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                break
    elif "body" in payload and payload["body"].get("data"):
        body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

    return {
        "id": msg["id"],
        "subject": headers.get("Subject", ""),
        "from": headers.get("From", ""),
        "to": headers.get("To", ""),
        "date": headers.get("Date", ""),
        "body": body,
        "snippet": msg.get("snippet", ""),
    }
