import asyncio
import logging
import time
from datetime import datetime
from aiogram import Router, Bot, types
from aiogram.enums import ChatAction
from app.config.settings import settings
from app.database.connection import async_session
from app.database.repository import (
    upsert_business_connection,
    get_business_connection,
    remove_stale_user_connections,
    add_chat_message,
    get_chat_history,
    get_pinned_chat_model,
    set_pinned_chat_model,
    get_greeting_date,
    set_greeting_date,
)
from app.services.ai.factory import ai_factory
from app.services.media import media_service
from app.services.animation import run_aiogram_animation, ANIMATIONS
from app.plugins.manager import plugin_manager

logger = logging.getLogger(__name__)
router = Router()

_last_ai_reply: dict = {}

async def send_text_fb(bot: Bot, chat_id: int, text: str, conn_id: str, parse_mode=None):
    try:
        await bot.send_message(chat_id=chat_id, text=text, business_connection_id=conn_id, parse_mode=parse_mode)
    except Exception:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)

@router.business_connection()
async def handle_business_connection(business_connection: types.BusinessConnection, bot: Bot):
    conn_id = business_connection.id
    user = business_connection.user
    user_id = user.id
    username = f"@{user.username}" if user.username else (user.full_name or "akkount egasi")

    async with async_session() as session:
        await remove_stale_user_connections(session, user_id, conn_id)
        await upsert_business_connection(
            session=session,
            connection_id=conn_id,
            user_id=user_id,
            user_chat_id=user_id,
            username=username,
            first_name=user.first_name or "",
            last_name=user.last_name or "",
            can_reply=business_connection.can_reply,
            is_enabled=True,
            is_approved=True,
            rights=business_connection.model_dump() if hasattr(business_connection, "model_dump") else None
        )

    logger.info(f"Business Connection registered: conn_id={conn_id}, user_id={user_id}, username={username}")

    try:
        await bot.send_message(
            chat_id=user_id,
            text=f"✅ Telegram Business hisobingiz botga ulandi!\n👤 Hisob: {username}\n⚙️ Sozlamalar: /settings",
            parse_mode=None
        )
    except Exception as e:
        logger.warning(f"Could not notify user {user_id}: {e}")

@router.business_message()
async def handle_business_message(message: types.Message, bot: Bot):
    conn_id = message.business_connection_id
    if not conn_id:
        return

    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else 0

    async with async_session() as session:
        conn = await get_business_connection(session, conn_id)
        if not conn:
            # Recover connection
            try:
                bc = await bot.get_business_connection(connection_id=conn_id)
                username = f"@{bc.user.username}" if bc.user.username else (bc.user.full_name or "akkount egasi")
                conn = await upsert_business_connection(
                    session=session,
                    connection_id=conn_id,
                    user_id=bc.user.id,
                    user_chat_id=bc.user.id,
                    username=username,
                    first_name=bc.user.first_name or "",
                    last_name=bc.user.last_name or "",
                    can_reply=bc.can_reply,
                    is_enabled=True,
                    is_approved=True
                )
            except Exception as e:
                logger.warning(f"Failed to recover connection {conn_id}: {e}")
                return

    owner_uid = conn.user_id
    text = (message.text or message.caption or "").strip()

    # ── OWNER MESSAGES ──────────────────────────────────────
    if user_id and user_id == owner_uid:
        if text.lower() == ".ok":
            try:
                await bot.delete_business_messages(business_connection_id=conn_id, message_ids=[message.message_id])
            except Exception:
                pass
            if message.reply_to_message:
                await media_service.save_temporary_media(bot, message, owner_uid)
            return

        if text.startswith(".") and len(text) > 1:
            parts = text.split(maxsplit=1)
            cmd_word = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""

            try:
                await bot.delete_business_messages(business_connection_id=conn_id, message_ids=[message.message_id])
            except Exception:
                pass

            if cmd_word == ".ping":
                t0 = time.time()
                m = await bot.send_message(chat_id=chat_id, text="✅ <b>Ping: Tekshirilmoqda...</b>", business_connection_id=conn_id, parse_mode="HTML")
                t1 = time.time()
                ms = round((t1 - t0) * 1000)
                await bot.edit_message_text(chat_id=chat_id, message_id=m.message_id, text=f"✅ <b>Ping: {ms} ms</b>", business_connection_id=conn_id, parse_mode="HTML")
                return

            anim_name = cmd_word.replace(".", "")
            if anim_name in ANIMATIONS:
                asyncio.create_task(run_aiogram_animation(bot, chat_id, anim_name, conn_id=conn_id))
                return

            handled = await plugin_manager.dispatch(cmd_word, bot, message, conn_id, args)
            if not handled:
                await send_text_fb(bot, chat_id, f"❓ Noma'lum buyruq: <code>{cmd_word}</code>", conn_id, parse_mode="HTML")
            return

        # Owner's normal message → record as assistant history
        if text:
            async with async_session() as session:
                await add_chat_message(session, conn_id, chat_id, "assistant", text)
        return

    # ── CUSTOMER MESSAGE — AUTO REPLY ────────────────────────
    if not conn.is_enabled:
        return
    if user_id == 0 or text.startswith("."):
        return

    now = time.time()
    if chat_id in _last_ai_reply and now - _last_ai_reply[chat_id] < settings.rate_limit_seconds:
        return

    today = datetime.now().strftime("%Y-%m-%d")
    async with async_session() as session:
        last_g = await get_greeting_date(session, chat_id)
        first_msg_today = last_g != today
        if first_msg_today:
            await set_greeting_date(session, chat_id, today)

    try:
        await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING, business_connection_id=conn_id)
    except Exception:
        pass

    # Build input contents
    contents = []
    log_content = text
    if message.photo:
        contents = await media_service.process_photo(bot, message.photo, message.caption or "")
        log_content = f"[Rasm] {message.caption or ''}"
    elif message.voice:
        contents = await media_service.process_voice(bot, message.voice)
        log_content = "[Ovozli xabar]"
    elif message.text:
        contents = [message.text]
    else:
        contents = [text or "Salom!"]

    async with async_session() as session:
        history = await get_chat_history(session, conn_id, chat_id, limit=settings.max_history_length)
        pinned_model = await get_pinned_chat_model(session, conn_id, chat_id)
        await add_chat_message(session, conn_id, chat_id, "user", log_content)

    history_text = ""
    if history:
        history_text = "Oldingi suhbat:\n" + "\n".join([f"{'Mijoz' if h.role == 'user' else 'Yordamchi'}: {h.content}" for h in history]) + "\nYangi xabar:\n"
        contents.insert(0, history_text)

    owner_handle = conn.username or conn.first_name or "akkount egasi"
    sys_prompt = conn.system_prompt or (
        f"Sen {owner_handle} ning shaxsiy yordamchisisan. "
        f"Vazifang: kelgan murojaatlarga o'zbek tilida javob berish. "
        f"1. Faqat o'zbek tilida yoz; o'zingni 'shaxsiy yordamchiman' deb tanishtir. "
        f"2. HAR XABARDA SALOM BERMA! "
        f"3. Javoblar to'liq va foydali bo'lsin."
    )

    selected_model = pinned_model or conn.model or settings.default_model
    reply_text = await ai_factory.generate_response(contents, sys_prompt, preferred_model=selected_model)
    _last_ai_reply[chat_id] = time.time()

    async with async_session() as session:
        await add_chat_message(session, conn_id, chat_id, "assistant", reply_text)

    await send_text_fb(bot, chat_id, reply_text, conn_id, parse_mode=None)
