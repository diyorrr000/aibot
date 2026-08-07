"""
In-memory storage for chat histories and business connection settings.
Includes Admin control functions for approving/disapproving connections.
"""
import json
import os
from collections import defaultdict
from typing import List, Dict, Any

from config import settings

# Strict Admin ID
ADMIN_ID = 7306854093

# Unicode bold digits for the profile clock (.soat) — names can't use markdown
BOLD_DIGITS = {
    '0': '𝟎', '1': '𝟏', '2': '𝟐', '3': '𝟑', '4': '𝟒',
    '5': '𝟓', '6': '𝟔', '7': '𝟕', '8': '𝟖', '9': '𝟗',
    ':': ':', ' ': ' ',
}

def to_bold_time(time_str: str) -> str:
    return "".join(BOLD_DIGITS.get(c, c) for c in time_str)

# chat_id -> list of {"role": "user"/"assistant", "content": ...}
chat_histories: Dict[int, List[Dict[str, Any]]] = defaultdict(list)

# connection_id -> {"system_prompt": str, "is_enabled": bool, "is_approved": bool, "user_id": int, "username": str}
connection_settings: Dict[str, Dict[str, Any]] = {}

# Per-chat AI model pin: "conn_id:chat_id" -> model name ("claude"/"grok"/"gpt").
# Once an AI starts answering in a chat it stays there until changed explicitly.
chat_models: Dict[str, str] = {}

# Per-chat "greeted today" tracking — the AI greets a customer only once a day
# and then continues the conversation naturally without re-greeting.
greeting_dates: Dict[str, str] = {}   # chat_id -> "YYYY-MM-DD"
GREETING_FILE = "database/greeting_dates.json"

# ── Disk persistence ───────────────────────────────────────
# connection_settings / chat_models are in-memory. After a server restart they
# would be empty, which breaks owner commands in every chat except the bot's
# private chat. Persisting them lets commands work everywhere even after restarts.
CONNECTIONS_FILE = "database/connections.json"
MODELS_FILE = "database/chat_models.json"


def _load_json(path: str) -> Dict[str, Any]:
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
    except Exception:
        pass
    return {}


def _save_json(path: str, data: dict):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _load_persisted():
    saved = _load_json(CONNECTIONS_FILE)
    for conn_id, conn in saved.items():
        if isinstance(conn, dict):
            connection_settings[conn_id] = conn
    saved_models = _load_json(MODELS_FILE)
    for key, model in saved_models.items():
        if isinstance(model, str):
            chat_models[key] = model
    saved_greetings = _load_json(GREETING_FILE)
    for cid, d in saved_greetings.items():
        if isinstance(d, str):
            greeting_dates[cid] = d


def get_chat_model(conn_id: str, chat_id: int) -> str:
    return chat_models.get(f"{conn_id}:{chat_id}")

def set_chat_model(conn_id: str, chat_id: int, model: str):
    chat_models[f"{conn_id}:{chat_id}"] = model
    _save_json(MODELS_FILE, chat_models)

def get_greeting_date(chat_id: int) -> str:
    return greeting_dates.get(str(chat_id), "")

def set_greeting_date(chat_id: int, date_str: str):
    greeting_dates[str(chat_id)] = date_str
    _save_json(GREETING_FILE, greeting_dates)

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
            "is_approved": True,   # No manual approval — the bot works immediately
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
    _save_json(CONNECTIONS_FILE, connection_settings)

def clear_other_connections(keep_conn_id: str, keep_user_id: int):
    """Remove the SAME user's older connections, keeping only their newest one.
    Other users' connections are never touched."""
    stale = [
        cid for cid, s in connection_settings.items()
        if cid != keep_conn_id and s.get("user_id") == keep_user_id
    ]
    for cid in stale:
        connection_settings.pop(cid, None)
    if stale:
        _save_json(CONNECTIONS_FILE, connection_settings)

def clear_all_connections():
    """Delete every stored business connection."""
    connection_settings.clear()
    _save_json(CONNECTIONS_FILE, connection_settings)

_load_persisted()

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


