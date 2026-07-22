import logging
from aiogram import Router, types, Bot, F
from aiogram.enums import ChatAction
from aiogram.filters import Command, CommandObject

from storage import (
    get_conn_settings, 
    set_conn_setting, 
    clear_history, 
    connection_settings,
    add_message,
    get_history
)
from config import settings
from services.gemini_service import gemini_service
from services.media_service import media_service

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


@router.message(F.chat.type == "private")
async def handle_private_message(message: types.Message, bot: Bot):
    # 1. Check if user is replying with ".ok" to save temporary media
    if message.text and message.text.strip().lower() == ".ok" and message.reply_to_message:
        success = await media_service.save_temporary_media(bot, message, message.chat.id)
        if success:
            await message.reply("✅ Media shaxsiy chatingizga muvaffaqiyatli saqlandi!")
        else:
            await message.reply("❌ Mediani saqlashda xatolik yuz berdi (muddati o'tgan yoki yuklab bo'lmaydi).")
        return

    # 2. Send typing action
    try:
        await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    except Exception:
        pass

    # 3. Process media content
    gemini_contents = []
    log_content = ""

    if message.photo:
        gemini_contents = await media_service.process_photo(bot, message.photo, message.caption or "")
        log_content = f"[Rasm] {message.caption or ''}"
    elif message.voice:
        gemini_contents = await media_service.process_voice(bot, message.voice)
        log_content = "[Ovozli xabar]"
    elif message.document:
        gemini_contents = await media_service.process_document(bot, message.document, message.caption or "")
        log_content = f"[Hujjat: {message.document.file_name}]"
    elif message.text:
        gemini_contents = [message.text]
        log_content = message.text
    else:
        gemini_contents = ["Kechirasiz, ushbu turdagi xabarlarni hali qo'llab-quvvatlamayman."]
        log_content = "[Qo'llab-quvvatlanmaydigan media]"

    # 4. Build chat history context
    history = get_history(message.chat.id, limit=settings.max_history_length)
    history_text = ""
    if history:
        history_text = "Oldingi suhbat:\n"
        for h in history:
            role_label = "Foydalanuvchi" if h["role"] == "user" else "Yordamchi"
            history_text += f"{role_label}: {h['content']}\n"
        history_text += "\nYangi xabar:\n"

    final_contents = []
    if history_text:
        final_contents.append(history_text)
    final_contents.extend(gemini_contents)

    add_message(message.chat.id, "user", log_content)

    # 5. Generate response using Gemini 2.5 Flash Lite
    try:
        reply_text = await gemini_service.generate_response(
            contents=final_contents,
            system_prompt=settings.default_system_prompt,
            model="gemini-2.5-flash-lite"
        )
    except Exception as e:
        logger.error(f"Gemini API error in private chat: {e}", exc_info=True)
        reply_text = "Kechirasiz, vaqtinchalik xatolik yuz berdi. Iltimos, birozdan so'ng qayta urinib ko'ring."

    add_message(message.chat.id, "assistant", reply_text)

    # 6. Send reply to user
    try:
        await message.answer(text=reply_text, parse_mode="Markdown")
    except Exception:
        await message.answer(text=reply_text)

