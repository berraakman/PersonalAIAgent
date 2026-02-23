"""Google Calendar service – list, create, update, delete events."""

from datetime import datetime, timedelta
from typing import Optional

from googleapiclient.discovery import build

from app.services.google_auth import get_credentials


def _get_service():
    creds = get_credentials()
    if not creds:
        raise PermissionError("Google hesabı bağlı değil.")
    return build("calendar", "v3", credentials=creds)


def list_events(
    max_results: int = 10,
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    calendar_id: str = "primary",
) -> list[dict]:
    """List upcoming events from Google Calendar."""
    service = _get_service()
    if not time_min:
        time_min = datetime.utcnow().isoformat() + "Z"

    kwargs = {
        "calendarId": calendar_id,
        "timeMin": time_min,
        "maxResults": max_results,
        "singleEvents": True,
        "orderBy": "startTime",
    }
    if time_max:
        kwargs["timeMax"] = time_max

    results = service.events().list(**kwargs).execute()
    events = []
    for event in results.get("items", []):
        events.append({
            "id": event["id"],
            "summary": event.get("summary", "(Başlıksız)"),
            "start": event["start"].get("dateTime", event["start"].get("date")),
            "end": event["end"].get("dateTime", event["end"].get("date")),
            "location": event.get("location", ""),
            "description": event.get("description", ""),
            "link": event.get("htmlLink", ""),
        })
    return events


def create_event(
    summary: str,
    start_time: str,
    end_time: str,
    description: str = "",
    location: str = "",
    attendees: Optional[list[str]] = None,
    calendar_id: str = "primary",
    timezone: str = "Europe/Istanbul",
) -> dict:
    """Create a new calendar event.

    Args:
        start_time / end_time: ISO 8601 datetime strings, e.g. "2026-03-01T10:00:00"
    """
    service = _get_service()
    event_body = {
        "summary": summary,
        "description": description,
        "location": location,
        "start": {"dateTime": start_time, "timeZone": timezone},
        "end": {"dateTime": end_time, "timeZone": timezone},
    }
    if attendees:
        event_body["attendees"] = [{"email": e} for e in attendees]

    event = service.events().insert(calendarId=calendar_id, body=event_body).execute()
    return {
        "id": event["id"],
        "summary": event.get("summary"),
        "start": event["start"].get("dateTime"),
        "end": event["end"].get("dateTime"),
        "link": event.get("htmlLink", ""),
        "status": "created",
    }


def update_event(
    event_id: str,
    summary: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
    calendar_id: str = "primary",
    timezone: str = "Europe/Istanbul",
) -> dict:
    """Update an existing calendar event."""
    service = _get_service()
    event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()

    if summary:
        event["summary"] = summary
    if description is not None:
        event["description"] = description
    if location is not None:
        event["location"] = location
    if start_time:
        event["start"] = {"dateTime": start_time, "timeZone": timezone}
    if end_time:
        event["end"] = {"dateTime": end_time, "timeZone": timezone}

    updated = service.events().update(calendarId=calendar_id, eventId=event_id, body=event).execute()
    return {
        "id": updated["id"],
        "summary": updated.get("summary"),
        "status": "updated",
        "link": updated.get("htmlLink", ""),
    }


def delete_event(event_id: str, calendar_id: str = "primary") -> dict:
    """Delete a calendar event."""
    service = _get_service()
    service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
    return {"id": event_id, "status": "deleted"}
