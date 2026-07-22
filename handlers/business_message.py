import logging
from aiogram import Router, Bot, types
from aiogram.enums import ChatAction

from services.grok_service import grok_service
from services.media_service import media_service
from storage import get_conn_settings, add_message, get_history
from config import settings

logger = logging.getLogger(__name__)
router = Router()


@router.business_message()
async def handle_business_message(message: types.Message, bot: Bot):
    conn_id = message.business_connection_id
    if not conn_id:
        return

    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else 0
    conn = get_conn_settings(conn_id)

    if not conn.get("is_approved"):
        logger.info(f"Business connection {conn_id} is not approved by Admin. Skipping.")
        return

    if not conn.get("is_enabled") or not conn.get("can_reply", True):
        return

    # If business owner sent this message to the customer — record as assistant, skip reply
    if conn.get("user_id") and user_id == conn["user_id"]:
        # If the owner replied with ".ok" to save media
        if message.text and message.text.strip().lower() == ".ok" and message.reply_to_message:
            success = await media_service.save_temporary_media(bot, message, conn["user_id"])
            if success:
                await message.reply("✅ Media shaxsiy chatingizga muvaffaqiyatli saqlandi!", business_connection_id=conn_id)
            else:
                await message.reply("❌ Mediani yuklashda xatolik yuz berdi.", business_connection_id=conn_id)
            return

        if message.text:
            add_message(chat_id, "assistant", message.text)
        return

    # Send typing indicator
    try:
        await bot.send_chat_action(
            chat_id=chat_id,
            action=ChatAction.TYPING,
            business_connection_id=conn_id
        )
    except Exception as e:
        logger.warning(f"Typing action failed: {e}")

    # Build Gemini content
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

    # Build history context
    history = get_history(chat_id, limit=settings.max_history_length)
    history_text = ""
    if history:
        history_text = "Oldingi suhbat:\n"
        for h in history:
            role_label = "Mijoz" if h["role"] == "user" else "Yordamchi"
            history_text += f"{role_label}: {h['content']}\n"
        history_text += "\nYangi xabar:\n"

    final_contents = []
    if history_text:
        final_contents.append(history_text)
    final_contents.extend(gemini_contents)

    add_message(chat_id, "user", log_content)

    # Generate response
    try:
        reply_text = await grok_service.generate_response(
            contents=final_contents,
            system_prompt=conn.get("system_prompt", settings.default_system_prompt),
            model="grok-3"
        )
    except Exception as e:
        logger.error(f"Gemini API error: {e}", exc_info=True)
        reply_text = "Kechirasiz, vaqtinchalik xatolik yuz berdi. Iltimos, birozdan so'ng qayta urinib ko'ring."

    add_message(chat_id, "assistant", reply_text)

    # Reply on behalf of business account
    try:
        await message.answer(text=reply_text, business_connection_id=conn_id, parse_mode="Markdown")
    except Exception:
        await message.answer(text=reply_text, business_connection_id=conn_id)


@router.edited_business_message()
async def handle_edited_business_message(message: types.Message):
    logger.info(f"Edited business message: conn_id={message.business_connection_id}")


@router.deleted_business_messages()
async def handle_deleted_business_messages(event: types.BusinessMessagesDeleted):
    logger.info(f"Deleted messages: conn_id={event.business_connection_id}, ids={event.message_ids}")
