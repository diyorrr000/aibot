"""
In-memory storage for chat histories and business connection settings.
Includes Admin control functions for approving/disapproving connections.
"""
from collections import defaultdict
from typing import List, Dict, Any

from config import settings

# Strict Admin ID
ADMIN_ID = 7306854093

# chat_id -> list of {"role": "user"/"assistant", "content": ...}
chat_histories: Dict[int, List[Dict[str, Any]]] = defaultdict(list)

# connection_id -> {"system_prompt": str, "is_enabled": bool, "is_approved": bool, "user_id": int, "username": str}
connection_settings: Dict[str, Dict[str, Any]] = {}

def get_history(chat_id: int, limit: int = None) -> List[Dict[str, Any]]:
    history = chat_histories[chat_id]
    if limit:
        return history[-limit:]
    return list(history)

def add_message(chat_id: int, role: str, content: str):
    chat_histories[chat_id].append({"role": role, "content": content})
    if len(chat_histories[chat_id]) > settings.max_history_length:
        chat_histories[chat_id] = chat_histories[chat_id][-settings.max_history_length:]

def clear_history(chat_id: int):
    chat_histories[chat_id] = []

def get_conn_settings(connection_id: str) -> Dict[str, Any]:
    if connection_id not in connection_settings:
        connection_settings[connection_id] = {
            "system_prompt": settings.default_system_prompt,
            "is_enabled": True,
            "is_approved": True,  # Auto-approved — no admin confirmation needed
            "user_id": None,
            "username": "Noma'lum"
        }
    return connection_settings[connection_id]

def set_conn_setting(connection_id: str, **kwargs):
    s = get_conn_settings(connection_id)
    s.update(kwargs)
    connection_settings[connection_id] = s
