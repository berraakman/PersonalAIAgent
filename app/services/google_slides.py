"""Google Slides service – create presentations, add slides, insert text."""

from typing import Optional

from googleapiclient.discovery import build

from app.services.google_auth import get_credentials


def _get_service():
    creds = get_credentials()
    if not creds:
        raise PermissionError("Google hesabı bağlı değil.")
    return build("slides", "v1", credentials=creds)


def create_presentation(title: str) -> dict:
    """Create a new Google Slides presentation."""
    service = _get_service()
    body = {"title": title}
    presentation = service.presentations().create(body=body).execute()
    pres_id = presentation["presentationId"]
    return {
        "presentationId": pres_id,
        "title": title,
        "link": f"https://docs.google.com/presentation/d/{pres_id}/edit",
    }


def get_presentation(presentation_id: str) -> dict:
    """Get presentation metadata and slide info."""
    service = _get_service()
    pres = service.presentations().get(presentationId=presentation_id).execute()
    slides = []
    for slide in pres.get("slides", []):
        slide_info = {"objectId": slide["objectId"], "elements": []}
        for element in slide.get("pageElements", []):
            if "shape" in element and "text" in element["shape"]:
                text = ""
                for te in element["shape"]["text"].get("textElements", []):
                    if "textRun" in te:
                        text += te["textRun"]["content"]
                slide_info["elements"].append({"type": "text", "content": text.strip()})
        slides.append(slide_info)
    return {
        "presentationId": presentation_id,
        "title": pres.get("title", ""),
        "slideCount": len(slides),
        "slides": slides,
        "link": f"https://docs.google.com/presentation/d/{presentation_id}/edit",
    }


def add_slide(presentation_id: str, layout: str = "BLANK") -> dict:
    """Add a new slide to a presentation."""
    service = _get_service()
    requests = [
        {
            "createSlide": {
                "slideLayoutReference": {"predefinedLayout": layout},
            }
        }
    ]
    response = service.presentations().batchUpdate(
        presentationId=presentation_id, body={"requests": requests}
    ).execute()
    slide_id = response["replies"][0]["createSlide"]["objectId"]
    return {"status": "success", "slideId": slide_id, "presentationId": presentation_id}


def add_text_to_slide(
    presentation_id: str,
    slide_id: str,
    text: str,
    x: float = 100,
    y: float = 100,
    width: float = 500,
    height: float = 300,
) -> dict:
    """Add a text box with content to a specific slide."""
    service = _get_service()
    element_id = f"textbox_{slide_id[:8]}"
    requests = [
        {
            "createShape": {
                "objectId": element_id,
                "shapeType": "TEXT_BOX",
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {
                        "width": {"magnitude": width, "unit": "PT"},
                        "height": {"magnitude": height, "unit": "PT"},
                    },
                    "transform": {
                        "scaleX": 1,
                        "scaleY": 1,
                        "translateX": x,
                        "translateY": y,
                        "unit": "PT",
                    },
                },
            }
        },
        {
            "insertText": {
                "objectId": element_id,
                "insertionIndex": 0,
                "text": text,
            }
        },
    ]
    service.presentations().batchUpdate(
        presentationId=presentation_id, body={"requests": requests}
    ).execute()
    return {"status": "success", "elementId": element_id, "presentationId": presentation_id}
