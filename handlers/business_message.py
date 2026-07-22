import logging
from aiogram import Router, Bot, types, F
from aiogram.enums import ChatAction
from sqlalchemy.ext.asyncio import AsyncSession

from database.repository import (
    get_business_connection,
    get_or_create_settings,
    get_chat_history,
    add_chat_message
)
from services.openai_service import openai_service
from services.media_service import media_service
from config import settings

logger = logging.getLogger(__name__)
router = Router()

@router.business_message()
async def handle_business_message(
    message: types.Message,
    bot: Bot,
    session: AsyncSession
):
    """
    Handles incoming messages in a Telegram Business account context.
    """
    conn_id = message.business_connection_id
    if not conn_id:
        return

    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else 0

    # Fetch business connection details from DB
    connection = await get_business_connection(session, conn_id)
    if not connection or not connection.is_enabled or not connection.can_reply:
        logger.info(f"Business connection {conn_id} is disabled or cannot reply. Skipping.")
        return

    # Fetch settings
    biz_settings = await get_or_create_settings(
        session=session,
        connection_id=conn_id,
        user_id=connection.user_id,
        default_prompt=settings.default_system_prompt,
        default_model=settings.default_model
    )

    if not biz_settings.is_auto_reply_enabled:
        logger.info(f"Auto-reply is disabled for connection {conn_id}.")
        return

    # If the message is sent BY the business owner themselves to the customer
    if user_id == connection.user_id:
        logger.info("Message sent by business owner. Recording to history without auto-replying.")
        if message.text:
            await add_chat_message(session, conn_id, chat_id, "assistant", message.text)
        elif message.caption:
            await add_chat_message(session, conn_id, chat_id, "assistant", message.caption)
        return

    # Send typing indicator on behalf of business connection
    try:
        await bot.send_chat_action(
            chat_id=chat_id,
            action=ChatAction.TYPING,
            business_connection_id=conn_id
        )
    except Exception as e:
        logger.warning(f"Could not send typing action: {e}")

    # Process media content
    user_payload = None
    log_content = ""

    if message.photo:
        user_payload = await media_service.process_photo(bot, message.photo, message.caption or "")
        log_content = f"[Rasm] {message.caption or ''}"
    elif message.voice:
        user_payload = await media_service.process_voice(bot, message.voice)
        log_content = str(user_payload["content"])
    elif message.document:
        user_payload = await media_service.process_document(bot, message.document, message.caption or "")
        log_content = str(user_payload["content"])
    elif message.text:
        user_payload = {"role": "user", "content": message.text}
        log_content = message.text
    else:
        user_payload = {"role": "user", "content": "Kechirasiz, ushbu turdagi xabarlarni hali qo'llab-quvvatlamayman."}
        log_content = "[Qo'llab-quvvatlanmaydigan media]"

    # Retrieve chat history from DB
    raw_history = await get_chat_history(session, conn_id, chat_id, limit=settings.max_history_length)
    
    formatted_history = []
    for h in raw_history:
        formatted_history.append({
            "role": h.role,
            "content": h.content
        })
    
    # Append latest user message payload
    formatted_history.append(user_payload)

    # Save user message to DB
    await add_chat_message(session, conn_id, chat_id, "user", log_content)

    # Generate response from OpenAI GPT
    try:
        reply_text = await openai_service.generate_response(
            history=formatted_history,
            system_prompt=biz_settings.system_prompt,
            model=biz_settings.model_name
        )
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}", exc_info=True)
        reply_text = "Kechirasiz, so'rovingizni qayta ishlashda vaqtinchalik xatolik yuz berdi. Iltimos, birozdan so'ng qayta urinib ko'ring."

    # Save assistant reply to DB
    await add_chat_message(session, conn_id, chat_id, "assistant", reply_text)

    # Send reply back to customer using business_connection_id
    try:
        await message.answer(
            text=reply_text,
            business_connection_id=conn_id,
            parse_mode="Markdown"
        )
    except Exception as md_err:
        logger.warning(f"Markdown formatting error, sending as plain text: {md_err}")
        await message.answer(
            text=reply_text,
            business_connection_id=conn_id
        )

@router.edited_business_message()
async def handle_edited_business_message(message: types.Message):
    """
    Handles edited business messages.
    """
    logger.info(f"Edited business message received: conn_id={message.business_connection_id}, msg_id={message.message_id}")

@router.deleted_business_messages()
async def handle_deleted_business_messages(event: types.BusinessMessagesDeleted):
    """
    Handles deleted business messages.
    """
    logger.info(f"Deleted business messages event: conn_id={event.business_connection_id}, chat_id={event.chat.id}, msg_ids={event.message_ids}")
