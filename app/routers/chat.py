"""Chat routes – handles text and voice-based chat with the AI agent."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional

from app.services.ai_agent import chat
from app.services.google_auth import is_authenticated

router = APIRouter(prefix="/api", tags=["Chat"])

# In-memory conversation storage (per-session in production you'd use a DB)
_conversations: dict[str, list[dict]] = {}


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"


class ChatResponse(BaseModel):
    reply: str
    session_id: str


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """Process a text chat message through the AI agent."""
    if not is_authenticated():
        return ChatResponse(
            reply="⚠️ Google hesabınız bağlı değil. Lütfen önce sol panelden Google hesabınızla giriş yapın.",
            session_id=req.session_id,
        )

    history = _conversations.get(req.session_id, [])

    try:
        reply, updated_history = await chat(req.message, history)
        _conversations[req.session_id] = updated_history

        # Keep history manageable (last 30 messages)
        if len(_conversations[req.session_id]) > 30:
            _conversations[req.session_id] = _conversations[req.session_id][-30:]

        return ChatResponse(reply=reply, session_id=req.session_id)
    except Exception as e:
        return ChatResponse(
            reply=f"❌ Bir hata oluştu: {str(e)}",
            session_id=req.session_id,
        )


@router.post("/chat/clear")
async def clear_chat(session_id: str = "default"):
    """Clear conversation history for a session."""
    _conversations.pop(session_id, None)
    return {"status": "cleared", "session_id": session_id}


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for real-time chat (used by voice input)."""
    await websocket.accept()
    session_id = "ws_default"
    history = _conversations.get(session_id, [])

    try:
        while True:
            data = await websocket.receive_text()

            if not is_authenticated():
                await websocket.send_json({
                    "reply": "⚠️ Google hesabınız bağlı değil.",
                    "type": "error",
                })
                continue

            try:
                reply, history = await chat(data, history)
                _conversations[session_id] = history

                if len(_conversations[session_id]) > 30:
                    _conversations[session_id] = _conversations[session_id][-30:]

                await websocket.send_json({
                    "reply": reply,
                    "type": "message",
                })
            except Exception as e:
                await websocket.send_json({
                    "reply": f"❌ Hata: {str(e)}",
                    "type": "error",
                })
    except WebSocketDisconnect:
        pass
