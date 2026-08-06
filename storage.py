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

# Global admin settings
admin_settings: Dict[str, Any] = {
    "clock_enabled": False,  # Off by default, Admin turns it ON via /admin or /clock_on
}

def is_clock_enabled() -> bool:
    return admin_settings.get("clock_enabled", False)

def set_clock_enabled(enabled: bool):
    admin_settings["clock_enabled"] = enabled

def get_conn_settings(connection_id: str) -> Dict[str, Any]:
    if connection_id not in connection_settings:
        connection_settings[connection_id] = {
            "system_prompt": settings.default_system_prompt,
            "is_enabled": False,
            "is_approved": False,  # Not approved until business_connection update + admin approval
            "user_id": None,
            "username": "Noma'lum",
            "first_name": "",
            "last_name": "",
            "model": "claude"  # "claude" (Claude Haiku 4.5) or "grok" (Grok 4.3)
        }
    return connection_settings[connection_id]

def set_conn_setting(connection_id: str, **kwargs):
    s = get_conn_settings(connection_id)
    s.update(kwargs)
    connection_settings[connection_id] = s

# Userbot modules toggle state: user_id -> {"module_name": bool}
userbot_modules: Dict[int, Dict[str, bool]] = defaultdict(lambda: {
    "animations": True,
    "clock": True,
    "reactions": True,
    "auto_ad": False,      # Off by default for account safety
    "tts": True,
    "translator": True,
    "media": True,
    "ai": True,
    "ban_protection": True # Always ON by default for account safety
})

def get_userbot_modules(user_id: int) -> Dict[str, bool]:
    return userbot_modules[user_id]

def toggle_userbot_module(user_id: int, module_key: str) -> bool:
    mods = userbot_modules[user_id]
    mods[module_key] = not mods.get(module_key, True)
    return mods[module_key]

# ─────────────────────────────────────────────────────────
# TIMER CONFIG (.time / .settime) — persisted to disk
# ─────────────────────────────────────────────────────────
import json
import os

TIMER_FILE = "database/timer_config.json"

DEFAULT_TIMER = {
    "date": "01.01.2027",
    "msg": "🎄 <b>Yangi yilgacha {date} qoldi!</b>\n🥰 <i>Yangi yilni do'stlar davrasida kutamiz</i>"
}

def get_timer_config() -> Dict[str, str]:
    try:
        if os.path.exists(TIMER_FILE):
            with open(TIMER_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("date") and data.get("msg"):
                    return data
    except Exception:
        pass
    return dict(DEFAULT_TIMER)

def save_timer_config(date: str, msg: str):
    try:
        os.makedirs(os.path.dirname(TIMER_FILE), exist_ok=True)
        with open(TIMER_FILE, "w", encoding="utf-8") as f:
            json.dump({"date": date, "msg": msg}, f, ensure_ascii=False, indent=4)
    except Exception:
        pass


