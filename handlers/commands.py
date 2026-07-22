import logging
from aiogram import Router, types
from aiogram.filters import Command, CommandObject

from storage import get_conn_settings, set_conn_setting, clear_history, connection_settings
from config import settings

logger = logging.getLogger(__name__)
router = Router()


def find_user_connection(user_id: int):
    for conn_id, s in connection_settings.items():
        if s.get("user_id") == user_id and s.get("is_enabled"):
            return conn_id, s
    return None, None


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    conn_id, conn = find_user_connection(user_id)

    status = "❌ Ulangan Telegram Business hisobi topilmadi"
    if conn_id:
        status = f"✅ Telegram Business ga ulangan!"

    text = (
        f"👋 Salom, {message.from_user.first_name}!\n\n"
        f"Men SecureXXX xizmatkoriman — Telegram Business uchun Gemini 2.5 Flash Lite AI Asistentingiz.\n\n"
        f"Holat: {status}\n\n"
        f"Ulanish uchun:\n"
        f"1. Telegram Settings → Telegram Business → Chat Bots\n"
        f"2. @dicogpt_bot ni tanlang va ruxsatlarni bering\n\n"
        f"Buyruqlar:\n"
        f"/settings — joriy sozlamalar\n"
        f"/setprompt <matn> — tizim yo'riqnomasini o'zgartirish\n"
        f"/toggle — avto-javobni yoqish/o'chirish\n"
        f"/reset — suhbat tarixini tozalash"
    )
    await message.answer(text)


@router.message(Command("settings"))
async def cmd_settings(message: types.Message):
    user_id = message.from_user.id
    conn_id, conn = find_user_connection(user_id)

    if not conn_id:
        await message.answer("⚠️ Hali Telegram Business hisobiga ulanmagan.")
        return

    auto_status = "✅ Yoqilgan" if conn.get("is_enabled", True) else "❌ O'chirilgan"
    prompt = conn.get("system_prompt", settings.default_system_prompt)

    await message.answer(
        f"Sozlamalar:\n\n"
        f"Model: gemini-2.5-flash-lite\n"
        f"Avto-javob: {auto_status}\n\n"
        f"Tizim yo'riqnomasi:\n{prompt}"
    )


@router.message(Command("setprompt"))
async def cmd_set_prompt(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    conn_id, conn = find_user_connection(user_id)

    if not conn_id:
        await message.answer("⚠️ Hali Telegram Business hisobiga ulanmagan.")
        return

    new_prompt = command.args
    if not new_prompt:
        await message.answer("Yangi promptni kiriting:\n/setprompt Siz do'kon yordamchisisiz...")
        return

    set_conn_setting(conn_id, system_prompt=new_prompt)
    await message.answer("✅ Tizim yo'riqnomasi yangilandi!")


@router.message(Command("toggle"))
async def cmd_toggle(message: types.Message):
    user_id = message.from_user.id
    conn_id, conn = find_user_connection(user_id)

    if not conn_id:
        await message.answer("⚠️ Hali Telegram Business hisobiga ulanmagan.")
        return

    new_status = not conn.get("is_enabled", True)
    set_conn_setting(conn_id, is_enabled=new_status)

    if new_status:
        await message.answer("✅ Avto-javob yoqildi!")
    else:
        await message.answer("❌ Avto-javob o'chirildi!")


@router.message(Command("reset"))
async def cmd_reset(message: types.Message):
    clear_history(message.chat.id)
    await message.answer("✅ Suhbat tarixi tozalandi!")
