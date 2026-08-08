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
    get_all_business_connections,
    remove_stale_user_connections,
    add_chat_message,
    get_chat_history,
    get_pinned_chat_model,
    get_greeting_date,
    set_greeting_date,
)
from app.services.ai.factory import ai_factory
from app.services.media import media_service
from app.services.animation import run_aiogram_animation, ANIMATIONS
from app.plugins.manager import plugin_manager
from app.utils.helpers import clean_ai_markdown

logger = logging.getLogger(__name__)
router = Router()

_last_ai_reply: dict = {}

async def send_text_fb(bot: Bot, chat_id: int, text: str, conn_id: str, parse_mode="HTML"):
    cleaned_text = clean_ai_markdown(text) if parse_mode == "HTML" else text
    try:
        await bot.send_message(chat_id=chat_id, text=cleaned_text, business_connection_id=conn_id, parse_mode=parse_mode)
    except Exception as e:
        logger.warning(f"send_text_fb with {parse_mode} failed ({e}), falling back to parse_mode=None")
        try:
            await bot.send_message(chat_id=chat_id, text=text, business_connection_id=conn_id)
        except Exception:
            try:
                await bot.send_message(chat_id=chat_id, text=text)
            except Exception as e2:
                logger.error(f"Failed to send text fallback: {e2}")

async def keep_typing_active(bot: Bot, chat_id: int, conn_id: str, stop_event: asyncio.Event):
    """Sends typing action periodically until response is ready."""
    while not stop_event.is_set():
        try:
            await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING, business_connection_id=conn_id)
        except Exception:
            try:
                await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
            except Exception:
                pass
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=3.5)
        except asyncio.TimeoutError:
            pass

async def sync_all_business_connections(bot: Bot):
    try:
        async with async_session() as session:
            conns = await get_all_business_connections(session)
            for conn in conns:
                try:
                    bc = await bot.get_business_connection(connection_id=conn.connection_id)
                    if bc:
                        username = f"@{bc.user.username}" if bc.user.username else (bc.user.full_name or "akkount egasi")
                        await upsert_business_connection(
                            session=session,
                            connection_id=conn.connection_id,
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
                    logger.debug(f"Sync check for conn {conn.connection_id}: {e}")
    except Exception as e:
        logger.error(f"Error in sync_all_business_connections: {e}")

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
            text=f"✅ Telegram Business hisobingiz botga ulandi va faollashtirildi!\n👤 Hisob: {username}\n⚙️ Sozlamalar: /settings",
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

    # ── 1. ALL CHAT DOT COMMANDS ──────────────────────────────
    if text.startswith(".") and len(text) > 1:
        parts = text.split(maxsplit=1)
        cmd_word = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd_word == ".ok":
            try:
                await bot.delete_business_messages(business_connection_id=conn_id, message_ids=[message.message_id])
            except Exception:
                try:
                    await message.delete()
                except Exception:
                    pass
            if message.reply_to_message:
                await media_service.save_temporary_media(bot, message, owner_uid)
            return

        try:
            if user_id and (user_id == owner_uid or user_id in settings.admin_ids):
                await bot.delete_business_messages(business_connection_id=conn_id, message_ids=[message.message_id])
        except Exception:
            pass

        if cmd_word in (".help", ".co", ".func", ".komandalar"):
            await plugin_manager.dispatch(".co", bot, message, conn_id, args)
            return

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
            suggestion = plugin_manager.get_suggestion(cmd_word)
            if suggestion:
                best_match, usage = suggestion
                resp = (
                    f"❓ <b>Noma'lum buyruq:</b> <code>{cmd_word}</code>\n\n"
                    f"💡 <i>Siz <code>{best_match}</code> buyrug'ini nazarda tutdingizmi?</i>\n"
                    f"📝 <b>Namuna:</b> <code>{usage}</code>"
                )
            else:
                resp = (
                    f"❓ <b>Noma'lum buyruq:</b> <code>{cmd_word}</code>\n"
                    f"💡 Barcha buyruqlarni ko'rish uchun: <code>.co</code>"
                )
            await send_text_fb(bot, chat_id, resp, conn_id, parse_mode="HTML")
        return

    # ── 2. OWNER MESSAGES SAVE TO DB ─────────────────────────
    if user_id and (user_id == owner_uid or user_id in settings.admin_ids):
        if text:
            async with async_session() as session:
                await add_chat_message(session, conn_id, chat_id, "assistant", text)
        return

    # ── 3. CUSTOMER MESSAGE — AUTO REPLY ────────────────────────
    if not conn.is_enabled:
        return
    if user_id == 0:
        return

    now = time.time()
    rate_limit = max(settings.rate_limit_seconds, 2.0)
    if chat_id in _last_ai_reply and now - _last_ai_reply[chat_id] < rate_limit:
        return

    today = datetime.now().strftime("%Y-%m-%d")
    async with async_session() as session:
        last_g = await get_greeting_date(session, chat_id)
        first_msg_today = last_g != today
        if first_msg_today:
            await set_greeting_date(session, chat_id, today)

    # Launch continuous typing status loop
    typing_stop_event = asyncio.Event()
    typing_task = asyncio.create_task(keep_typing_active(bot, chat_id, conn_id, typing_stop_event))

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
        f"Siz {owner_handle} ning shaxsiy yordamchisisiz. "
        f"VAZIFANGIZ: Kelgan har qanday murojaat, savol yoki iboraga har tomonlama to'liq, keng va mazmunli javob berish.\n\n"
        f"QOIDALAR:\n"
        f"1. FAQAT va FAQAT O'zbek tilida yozing.\n"
        f"2. Nomi, shakli yoki AI modeli haqida so'ralganda (masalan 'sen kimsan', 'qaysi modelsan', 'AI misan'): HECH QACHON Google, Gemini, OpenAI, Claude, Anthropic, Sun'iy intellekt yoki AI model ekanligingizni AYTMANG! FAQAT 'Men {owner_handle} ning shaxsiy yordamchisiman' deb javob bering.\n"
        f"3. Mijoz slengda, imlo xatolari bilan yoki qisqa yozsa ham uning niyatini to'g'ri tushunib, savoliga keng va atroflicha javob bering. Javob topolmay qolmang.\n"
        f"4. Xabarlarda o'zingizni har safar qayta tanishtirmang ('Men shaxsiy yordamchiman' deb yozmang)."
    )

    if first_msg_today:
        sys_prompt += (
            f"\n\n5. Bugun bu mijozning kun davomidagi BIRINCHI murojaati. "
            f"Javobni bitta qisqa salom bilan boshlashingiz mumkin (masalan 'Assalomu alaykum! Qanday yordam bera olaman?'), so'ng murojaatiga to'liq javob bering."
        )
    else:
        sys_prompt += (
            f"\n\n5. Bugun bu chatda ALLAQACHON salomlashilgan va muloqot davom etmoqda. "
            f"HECH QANDAY salom berish yoki 'Assalomu alaykum' deyish MUMKIN EMAS! O'zingizni qayta tanishtirmang — FAQAT berilgan savolga to'g'ridan-to'g'ri javob bering."
        )

    try:
        selected_model = pinned_model or conn.model or settings.default_model
        reply_text = await ai_factory.generate_response(contents, sys_prompt, preferred_model=selected_model)
    finally:
        typing_stop_event.set()
        await typing_task

    _last_ai_reply[chat_id] = time.time()

    async with async_session() as session:
        await add_chat_message(session, conn_id, chat_id, "assistant", reply_text)

    await send_text_fb(bot, chat_id, reply_text, conn_id, parse_mode="HTML")
