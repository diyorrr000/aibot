import logging
from aiogram import Router, types, Bot, F
from aiogram.enums import ChatAction
from aiogram.filters import Command, CommandObject

from storage import (
    ADMIN_ID,
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
        if s.get("user_id") == user_id:
            return conn_id, s
    return None, None


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id

    if user_id == ADMIN_ID:
        text = (
            f"👋 Assalomu alaykum, Bot Admini!\n\n"
            f"Siz botning boshqaruvchisi hisoblanasiz.\n"
            f"Ulangan barcha Telegram Business hisoblarini ko'rish, tasdiqlash (approve) "
            f"va ularning sozlamalarini boshqarish uchun /admin buyrug'ini yozing."
        )
        await message.answer(text, parse_mode=None)
        return

    # Regular business owners
    conn_id, conn = find_user_connection(user_id)

    status = "❌ Ulangan Telegram Business hisobi topilmadi"
    if conn_id:
        if conn.get("is_approved"):
            status = "✅ Telegram Business ga ulangan va faol!"
        else:
            status = "⏳ Ulangan, lekin tasdiqlash kutilmoqda (Admin ruxsati kerak)"

    text = (
        f"👋 Salom, {message.from_user.first_name}!\n\n"
        f"Men SecureXXX xizmatkoriman — Telegram Business uchun Gemini 2.5 Flash Lite AI Asistentingiz.\n\n"
        f"Ulanish holati: {status}\n\n"
        f"Ulanish uchun:\n"
        f"1. Telegram Settings -> Telegram Business -> Chat Bots\n"
        f"2. @dicogpt_bot ni tanlang va ruxsatlarni bering\n"
        f"3. Ulangach, bot ishlashi uchun bot admini (7306854093) tasdiqlashini kuting."
    )
    await message.answer(text, parse_mode=None)


@router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⚠️ Ushbu buyruq faqat bot admini (7306854093) uchun amal qiladi.", parse_mode=None)
        return

    if not connection_settings:
        await message.answer("ℹ️ Hozircha hech qanday Telegram Business hisobi ulanmagan.", parse_mode=None)
        return

    msg = "📋 Ulangan Telegram Business hisoblari ro'yxati:\n\n"
    for conn_id, s in connection_settings.items():
        approved_status = "✅ TASDIQLANGAN" if s.get("is_approved") else "⏳ TASDIQ KUTILMOQDA"
        auto_status = "Yoqilgan" if s.get("is_enabled") else "O'chirilgan"
        prompt = s.get("system_prompt", settings.default_system_prompt)
        if len(prompt) > 80:
            prompt = prompt[:77] + "..."

        msg += (
            f"🆔 ID: {conn_id}\n"
            f"👤 Foydalanuvchi: @{s.get('username')}\n"
            f"🔒 Holat: {approved_status}\n"
            f"⚡ Avto-javob: {auto_status}\n"
            f"📝 Prompt: {prompt}\n\n"
        )

    msg += (
        "✍️ Sozlash buyruqlari:\n"
        "/approve <connection_id> - ruxsat berish\n"
        "/disapprove <connection_id> - ruxsatni olish\n"
        "/setprompt <connection_id> <prompt matni> - promptni o'zgartirish\n"
        "/toggle <connection_id> - yoqish/o'chirish"
    )
    await message.answer(msg, parse_mode=None)


@router.message(Command("approve"))
async def cmd_approve(message: types.Message, command: CommandObject, bot: Bot):
    if message.from_user.id != ADMIN_ID:
        return

    conn_id = command.args
    if not conn_id or conn_id not in connection_settings:
        await message.answer("⚠️ Iltimos, ro'yxatdagi to'g'ri Connection ID ni kiriting. Masalan: /approve conn_id_shu_yerda")
        return

    set_conn_setting(conn_id, is_approved=True)
    conn = get_conn_settings(conn_id)
    
    await message.answer(f"✅ Connection {conn_id} muvaffaqiyatli tasdiqlandi!")
    
    # Notify the owner
    if conn.get("user_id"):
        try:
            await bot.send_message(
                chat_id=conn["user_id"], 
                text="🎉 Botingiz admin tomonidan tasdiqlandi! Endi Telegram Business avto-javoblari faol ishlaydi."
            )
        except Exception as e:
            logger.warning(f"Could not notify connection owner: {e}")


@router.message(Command("disapprove"))
async def cmd_disapprove(message: types.Message, command: CommandObject, bot: Bot):
    if message.from_user.id != ADMIN_ID:
        return

    conn_id = command.args
    if not conn_id or conn_id not in connection_settings:
        await message.answer("⚠️ Iltimos, ro'yxatdagi to'g'ri Connection ID ni kiriting.")
        return

    set_conn_setting(conn_id, is_approved=False)
    conn = get_conn_settings(conn_id)

    await message.answer(f"❌ Connection {conn_id} tasdiqlash holati bekor qilindi.")

    # Notify the owner
    if conn.get("user_id"):
        try:
            await bot.send_message(
                chat_id=conn["user_id"], 
                text="⚠️ Sizning Telegram Business ulanishingiz admin tomonidan to'xtatildi."
            )
        except Exception as e:
            logger.warning(f"Could not notify connection owner: {e}")


@router.message(Command("setprompt"))
async def cmd_set_prompt(message: types.Message, command: CommandObject):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⚠️ Ushbu buyruq faqat bot admini (7306854093) uchun amal qiladi.")
        return

    args = command.args
    if not args:
        await message.answer("⚠️ Foydalanish: /setprompt <connection_id> <prompt matni>")
        return

    # Split connection_id and prompt
    parts = args.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("⚠️ Foydalanish: /setprompt <connection_id> <prompt matni>")
        return

    conn_id, new_prompt = parts
    if conn_id not in connection_settings:
        await message.answer("⚠️ Bunday Connection ID topilmadi.")
        return

    set_conn_setting(conn_id, system_prompt=new_prompt)
    await message.answer(f"✅ Connection {conn_id} uchun tizim yo'riqnomasi yangilandi!")


@router.message(Command("toggle"))
async def cmd_toggle(message: types.Message, command: CommandObject):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⚠️ Ushbu buyruq faqat bot admini (7306854093) uchun amal qiladi.")
        return

    conn_id = command.args
    if not conn_id or conn_id not in connection_settings:
        await message.answer("⚠️ Foydalanish: /toggle <connection_id>")
        return

    conn = get_conn_settings(conn_id)
    new_status = not conn.get("is_enabled", True)
    set_conn_setting(conn_id, is_enabled=new_status)

    status_str = "Yoqildi" if new_status else "O'chirildi"
    await message.answer(f"✅ Connection {conn_id} uchun avto-javob {status_str}!")


@router.message(Command("settings"))
async def cmd_settings(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⚠️ Ushbu buyruq faqat bot admini (7306854093) uchun amal qiladi.")
        return
    await cmd_admin(message)


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
