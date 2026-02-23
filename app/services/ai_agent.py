"""AI Agent service – connects to the LLM and dispatches tool calls to Google services.

Uses a function-calling approach: the LLM receives a system prompt describing
available tools, and when it decides to use a tool, this module parses the
request and calls the appropriate Google service function.
"""

import json
import re
from typing import Optional

import httpx

from app.config import settings
from app.services import google_drive, google_docs, google_sheets, google_slides, google_calendar, google_gmail

# ---------------------------------------------------------------------------
# Tool definitions (sent to the LLM so it knows what it can call)
# ---------------------------------------------------------------------------

TOOLS = [
    # ----- Drive -----
    {
        "name": "drive_list_files",
        "description": "Google Drive'daki dosyaları listeler. query parametresi opsiyoneldir.",
        "parameters": {"query": "string (opsiyonel)", "page_size": "integer (varsayılan 20)"},
    },
    {
        "name": "drive_search_files",
        "description": "Google Drive'da dosya arar.",
        "parameters": {"name": "string – aranacak dosya adı"},
    },
    {
        "name": "drive_download_file",
        "description": "Google Drive'dan dosya indirir. file_id gereklidir.",
        "parameters": {"file_id": "string"},
    },
    {
        "name": "drive_create_folder",
        "description": "Google Drive'da klasör oluşturur.",
        "parameters": {"name": "string", "parent_id": "string (opsiyonel)"},
    },
    # ----- Docs -----
    {
        "name": "docs_create",
        "description": "Yeni bir Google Docs belgesi oluşturur.",
        "parameters": {"title": "string", "body_text": "string (opsiyonel)"},
    },
    {
        "name": "docs_read",
        "description": "Bir Google Docs belgesini okur. document_id gereklidir.",
        "parameters": {"document_id": "string"},
    },
    {
        "name": "docs_append_text",
        "description": "Bir Google Docs belgesine metin ekler.",
        "parameters": {"document_id": "string", "text": "string"},
    },
    {
        "name": "docs_find_replace",
        "description": "Bir Google Docs belgesinde bul ve değiştir yapar.",
        "parameters": {"document_id": "string", "find": "string", "replace": "string"},
    },
    # ----- Sheets -----
    {
        "name": "sheets_create",
        "description": "Yeni bir Google Spreadsheet oluşturur.",
        "parameters": {"title": "string", "headers": "list[string] (opsiyonel)"},
    },
    {
        "name": "sheets_read",
        "description": "Bir Google Spreadsheet'ten veri okur.",
        "parameters": {"spreadsheet_id": "string", "range_name": "string (varsayılan A1:Z1000)"},
    },
    {
        "name": "sheets_write",
        "description": "Bir Google Spreadsheet'e veri yazar.",
        "parameters": {"spreadsheet_id": "string", "range_name": "string", "values": "list[list]"},
    },
    {
        "name": "sheets_append_rows",
        "description": "Bir Google Spreadsheet'e satır ekler.",
        "parameters": {"spreadsheet_id": "string", "values": "list[list]"},
    },
    # ----- Slides -----
    {
        "name": "slides_create",
        "description": "Yeni bir Google Slides sunumu oluşturur.",
        "parameters": {"title": "string"},
    },
    {
        "name": "slides_get",
        "description": "Bir Google Slides sunumunun bilgilerini getirir.",
        "parameters": {"presentation_id": "string"},
    },
    {
        "name": "slides_add_slide",
        "description": "Bir sunuma yeni slayt ekler.",
        "parameters": {"presentation_id": "string", "layout": "string (varsayılan BLANK)"},
    },
    {
        "name": "slides_add_text",
        "description": "Bir slayda metin kutusu ekler.",
        "parameters": {"presentation_id": "string", "slide_id": "string", "text": "string"},
    },
    # ----- Calendar -----
    {
        "name": "calendar_list_events",
        "description": "Google Calendar'daki yaklaşan etkinlikleri listeler.",
        "parameters": {"max_results": "integer (varsayılan 10)"},
    },
    {
        "name": "calendar_create_event",
        "description": "Google Calendar'a yeni etkinlik ekler.",
        "parameters": {
            "summary": "string – etkinlik başlığı",
            "start_time": "string – ISO 8601 (örn: 2026-03-01T10:00:00)",
            "end_time": "string – ISO 8601",
            "description": "string (opsiyonel)",
            "location": "string (opsiyonel)",
            "attendees": "list[string] – e-posta listesi (opsiyonel)",
        },
    },
    {
        "name": "calendar_update_event",
        "description": "Mevcut bir takvim etkinliğini günceller.",
        "parameters": {
            "event_id": "string",
            "summary": "string (opsiyonel)",
            "start_time": "string (opsiyonel)",
            "end_time": "string (opsiyonel)",
        },
    },
    {
        "name": "calendar_delete_event",
        "description": "Bir takvim etkinliğini siler.",
        "parameters": {"event_id": "string"},
    },
    # ----- Gmail -----
    {
        "name": "gmail_send",
        "description": "Gmail üzerinden e-posta gönderir.",
        "parameters": {
            "to": "string – alıcı e-posta",
            "subject": "string – konu",
            "body": "string – e-posta gövdesi (HTML destekli)",
            "cc": "string (opsiyonel)",
            "bcc": "string (opsiyonel)",
        },
    },
    {
        "name": "gmail_create_draft",
        "description": "Gmail'de taslak oluşturur.",
        "parameters": {
            "to": "string",
            "subject": "string",
            "body": "string",
            "cc": "string (opsiyonel)",
            "bcc": "string (opsiyonel)",
        },
    },
    {
        "name": "gmail_list_messages",
        "description": "Gmail'deki mesajları listeler.",
        "parameters": {"query": "string (opsiyonel)", "max_results": "integer (varsayılan 10)"},
    },
    {
        "name": "gmail_get_message",
        "description": "Bir e-postanın tüm detaylarını getirir.",
        "parameters": {"message_id": "string"},
    },
]


# ---------------------------------------------------------------------------
# Tool dispatcher
# ---------------------------------------------------------------------------

def _dispatch_tool(name: str, args: dict) -> dict:
    """Call the actual Google service function based on the tool name."""
    try:
        if name == "drive_list_files":
            return {"result": google_drive.list_files(args.get("query"), int(args.get("page_size", 20)))}
        elif name == "drive_search_files":
            return {"result": google_drive.search_files(args["name"])}
        elif name == "drive_download_file":
            _, filename = google_drive.download_file(args["file_id"])
            return {"result": f"'{filename}' dosyası başarıyla indirildi. İndirme bağlantısını kullanıcıya sağlayın."}
        elif name == "drive_create_folder":
            return {"result": google_drive.create_folder(args["name"], args.get("parent_id"))}
        elif name == "docs_create":
            return {"result": google_docs.create_document(args["title"], args.get("body_text"))}
        elif name == "docs_read":
            return {"result": google_docs.read_document(args["document_id"])}
        elif name == "docs_append_text":
            return {"result": google_docs.append_text(args["document_id"], args["text"])}
        elif name == "docs_find_replace":
            return {"result": google_docs.find_and_replace(args["document_id"], args["find"], args["replace"])}
        elif name == "sheets_create":
            headers = args.get("headers")
            if isinstance(headers, str):
                headers = json.loads(headers)
            return {"result": google_sheets.create_spreadsheet(args["title"], headers)}
        elif name == "sheets_read":
            return {"result": google_sheets.read_range(args["spreadsheet_id"], args.get("range_name", "A1:Z1000"))}
        elif name == "sheets_write":
            values = args["values"]
            if isinstance(values, str):
                values = json.loads(values)
            return {"result": google_sheets.write_range(args["spreadsheet_id"], args["range_name"], values)}
        elif name == "sheets_append_rows":
            values = args["values"]
            if isinstance(values, str):
                values = json.loads(values)
            return {"result": google_sheets.append_rows(args["spreadsheet_id"], values)}
        elif name == "slides_create":
            return {"result": google_slides.create_presentation(args["title"])}
        elif name == "slides_get":
            return {"result": google_slides.get_presentation(args["presentation_id"])}
        elif name == "slides_add_slide":
            return {"result": google_slides.add_slide(args["presentation_id"], args.get("layout", "BLANK"))}
        elif name == "slides_add_text":
            return {"result": google_slides.add_text_to_slide(args["presentation_id"], args["slide_id"], args["text"])}
        elif name == "calendar_list_events":
            return {"result": google_calendar.list_events(int(args.get("max_results", 10)))}
        elif name == "calendar_create_event":
            return {
                "result": google_calendar.create_event(
                    summary=args["summary"],
                    start_time=args["start_time"],
                    end_time=args["end_time"],
                    description=args.get("description", ""),
                    location=args.get("location", ""),
                    attendees=args.get("attendees"),
                )
            }
        elif name == "calendar_update_event":
            return {
                "result": google_calendar.update_event(
                    event_id=args["event_id"],
                    summary=args.get("summary"),
                    start_time=args.get("start_time"),
                    end_time=args.get("end_time"),
                )
            }
        elif name == "calendar_delete_event":
            return {"result": google_calendar.delete_event(args["event_id"])}
        elif name == "gmail_send":
            return {
                "result": google_gmail.send_email(
                    to=args["to"],
                    subject=args["subject"],
                    body=args["body"],
                    cc=args.get("cc", ""),
                    bcc=args.get("bcc", ""),
                )
            }
        elif name == "gmail_create_draft":
            return {
                "result": google_gmail.create_draft(
                    to=args["to"],
                    subject=args["subject"],
                    body=args["body"],
                    cc=args.get("cc", ""),
                    bcc=args.get("bcc", ""),
                )
            }
        elif name == "gmail_list_messages":
            return {"result": google_gmail.list_messages(args.get("query", ""), int(args.get("max_results", 10)))}
        elif name == "gmail_get_message":
            return {"result": google_gmail.get_message(args["message_id"])}
        else:
            return {"error": f"Bilinmeyen araç: {name}"}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """Sen, Berra AKMAN adlı kullanıcının kişisel yapay zeka asistanısın. Adın "BerrAI".

Kullanıcının Google hesabı ile tam entegre çalışıyorsun. Aşağıdaki araçları kullanabilirsin:

{tools_description}

## Kurallar:
1. Kullanıcının isteklerini anla ve eğer işlem yapman gerekiyorsa mutlaka uygun aracı (tool) çağır.
2. Bir aracı çağırmak için SADECE aşağıdaki gibi bir JSON objesi çıktısı ver:
```json
{{"tool": "araç_adı", "args": {{"parametre_adi": "değeri"}}}}
```
3. ÇOK ÖNEMLİ: Eğer bir araç çağıracaksan, cevabına normal metin ekleme. Sadece JSON bloğunu ver.
4. ÇOK ÖNEMLİ: Birden fazla araç çağıracaksan, her bir JSON bloğunu ayrı ayrı ver.
5. Araç çağrıldıktan ve sonucu sana verildikten sonra (veya baştan bir araç kullanmana gerek yoksa) sonucu kullanıcıya Türkçe ve nazikçe özetle.
6. Tarih/saat: {current_date}
"""


def _build_system_prompt() -> str:
    """Build the system prompt with tool descriptions."""
    from datetime import datetime

    tools_text = ""
    for tool in TOOLS:
        parameters = tool.get("parameters", {})
        if isinstance(parameters, dict):
            params = ", ".join(f"{k}: {v}" for k, v in parameters.items())
        else:
            params = ""
        tools_text += f"- **{tool['name']}**: {tool['description']}\n  Parametreler: {params}\n"

    return SYSTEM_PROMPT.format(
        tools_description=tools_text,
        current_date=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )


# ---------------------------------------------------------------------------
# Chat function
# ---------------------------------------------------------------------------

async def chat(
    user_message: str,
    conversation_history: list[dict],
    max_tool_iterations: int = 5,
) -> tuple[str, list[dict]]:
    """Process a user message, potentially calling tools, and return a response.

    Returns:
        (assistant_reply, updated_conversation_history)
    """
    system_prompt = _build_system_prompt()

    # Build messages array
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})

    iteration = 0
    while iteration < max_tool_iterations:
        iteration += 1

        # Call the LLM
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.AI_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.AI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.AI_MODEL,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 4096,
                },
            )
            response.raise_for_status()
            data = response.json()

        assistant_content = data["choices"][0]["message"]["content"]

        # Check for tool calls in the response
        tool_calls = _extract_tool_calls(assistant_content)

        if not tool_calls:
            # No tool calls – this is the final answer
            # Clean the response (remove any thinking tags)
            clean_response = _clean_response(assistant_content)
            conversation_history.append({"role": "user", "content": user_message})
            conversation_history.append({"role": "assistant", "content": clean_response})
            return clean_response, conversation_history

        # Execute tool calls and feed results back
        messages.append({"role": "assistant", "content": assistant_content})

        tool_results = []
        for tc in tool_calls:
            result = _dispatch_tool(tc["tool"], tc["args"])
            tool_results.append(f"Araç `{tc['tool']}` sonucu:\n```json\n{json.dumps(result, ensure_ascii=False, indent=2)}\n```")

        combined_results = "\n\n".join(tool_results)
        messages.append({"role": "user", "content": f"Araç çağrı sonuçları:\n\n{combined_results}\n\nBu sonuçları kullanarak kullanıcıya anlaşılır bir yanıt ver."})

    # If we exceeded iterations, return last response
    conversation_history.append({"role": "user", "content": user_message})
    conversation_history.append({"role": "assistant", "content": "İşlem tamamlandı."})
    return "İşlem tamamlandı.", conversation_history


def _extract_tool_calls(content: str) -> list[dict]:
    """Extract tool_call JSON blocks from the assistant's response."""
    calls = []
    
    # First check explicit markdown code blocks
    pattern_blocks = r"```(?:json|tool_call)?\s*\n?(\{.*?\})\n?```"
    matches = re.findall(pattern_blocks, content, re.DOTALL)
    for match in matches:
        try:
            parsed = json.loads(match.strip())
            if isinstance(parsed, dict) and "tool" in parsed and "args" in parsed:
                calls.append(parsed)
        except json.JSONDecodeError:
            pass

    if calls:
        return calls

    # If no markdown blocks, use a robust brace-counting parser to find raw JSON objects
    start_idx = 0
    while True:
        try:
            start_idx = content.index("{", start_idx)
            brace_count = 0
            for i, char in enumerate(content[start_idx:]):
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    
                if brace_count == 0:
                    json_str = content[start_idx:start_idx + i + 1]
                    try:
                        parsed = json.loads(json_str)
                        if isinstance(parsed, dict) and "tool" in parsed and "args" in parsed:
                            calls.append(parsed)
                    except json.JSONDecodeError:
                        pass
                    # Jump past this object
                    start_idx = start_idx + i + 1
                    break
            else:
                # If we exit the loop without break, braces were unbalanced. Just break the while.
                break
        except ValueError:
            break

    return calls


def _clean_response(content: str) -> str:
    """Remove thinking tags and tool_call blocks from the response."""
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)
    content = re.sub(r"```(?:json|tool_call)?.*?```", "", content, flags=re.DOTALL)
    
    # Robust raw JSON removal using the same brace counting
    start_idx = 0
    cleaned_content = []
    
    while True:
        try:
            next_brace = content.index("{", start_idx)
            # Append anything before the brace
            cleaned_content.append(content[start_idx:next_brace])
            
            brace_count = 0
            found_object = False
            for i, char in enumerate(content[next_brace:]):
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    
                if brace_count == 0:
                    json_str = content[next_brace:next_brace + i + 1]
                    try:
                        parsed = json.loads(json_str)
                        if isinstance(parsed, dict) and "tool" in parsed and "args" in parsed:
                            # It's a tool call, skip adding it
                            found_object = True
                            start_idx = next_brace + i + 1
                            break
                    except json.JSONDecodeError:
                        pass
                    # Not a valid tool call, keep it
                    break
            
            if not found_object:
                # Add the `{` and move on
                cleaned_content.append("{")
                start_idx = next_brace + 1
                
        except ValueError:
            # No more braces
            cleaned_content.append(content[start_idx:])
            break
            
    return "".join(cleaned_content).strip()
