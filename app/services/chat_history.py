from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from app.services.mongo_client import get_chat_sessions_collection

MAX_HISTORY_TURNS = 6


def _col():
    return get_chat_sessions_collection()


def get_history(session_id: str, limit: int = MAX_HISTORY_TURNS) -> List[Dict[str, str]]:
    """Trả list {role, content} mới nhất, tối đa `limit` message."""
    doc = _col().find_one({"_id": session_id}, {"messages": 1})
    if not doc:
        return []
    messages = doc.get("messages") or []
    return messages[-limit:]


def append_message(session_id: str, role: str, content: str) -> None:
    """Lưu 1 message vào history (user hoặc assistant)."""
    now = datetime.now(timezone.utc)
    _col().update_one(
        {"_id": session_id},
        {
            "$push": {
                "messages": {
                    "role": role,
                    "content": content,
                    "ts": now,
                }
            },
            "$set": {"updated_at": now},
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,
    )


def format_history_for_prompt(history: List[Dict[str, Any]]) -> str:
    if not history:
        return "(không có lịch sử)"
    lines = []
    for m in history:
        role = m.get("role", "user")
        content = (m.get("content") or "").strip()
        if not content:
            continue
        label = "User" if role == "user" else "Assistant"
        if len(content) > 500:
            content = content[:500] + "..."
        lines.append(f"{label}: {content}")
    return "\n".join(lines) if lines else "(không có lịch sử)"