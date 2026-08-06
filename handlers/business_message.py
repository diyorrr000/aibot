import logging
from aiogram import Router, Bot, types
from aiogram.enums import ChatAction

from services.claude_service import claude_service
from services.media_service import media_service
from storage import get_conn_settings, add_message, get_history
from config import settings

logger = logging.getLogger(__name__)
router = Router()

# All valid userbot commands (for correction suggestions)
VALID_COMMANDS = [
    ".help", ".ping", ".ai", ".grok", ".tr", ".tts", ".co", ".love",
    ".clock", ".yt", ".tt", ".weather", ".q", ".meme", ".baza",
    ".anime", ".currency", ".lyrics", ".roulette", ".roleplay",
    ".read", ".upload", ".telegraph", ".gender", ".shortlink", ".ok",
]

COMMAND_HELP = {
    ".help":     "📋 Buyruqlar ro'yxati: shunchaki .help yozing.",
    ".ping":     "🏓 Ping: .ping — bot javob beradi.",
    ".ai":       "🤖 AI: .ai [savol] — Misol: .ai Toshkent qayerda?",
    ".grok":     "🌌 Grok: .grok [savol] — Misol: .grok kelajak haqida ayt",
    ".tr":       "🌐 Tarjima: .tr [til] [matn] — Misol: .tr en Salom dunyo",
    ".tts":      "🗣 Ovoz: .tts [matn] — Misol: .tts Assalomu alaykum",
    ".co":       "💫 Animatsiya: .co [matn] — Misol: .co salom",
    ".love":     "❤️ Love: .love",
    ".clock":    "🕒 Soat: .clock — Profilingizga O'zbekiston soatini qo'shadi",
    ".yt":       "▶️ YouTube: .yt [havola] — Misol: .yt https://youtu.be/xxx",
    ".tt":       "🎵 TikTok: .tt [havola] — Misol: .tt https://tiktok.com/xxx",
    ".weather":  "⛅ Ob-havo: .weather [shahar] — Misol: .weather Samarqand",
    ".q":        "💬 Iqtibos: .q — Random hikmatli gap",
    ".meme":     "😂 Meme: .meme — Random meme",
    ".baza":     "🗃 Ma'lumot: .baza [so'z] — Misol: .baza python",
    ".anime":    "🎌 Anime: .anime — Random anime rasm",
    ".currency": "💱 Valyuta: .currency [kod] — Misol: .currency USD",
    ".lyrics":   "🎵 Qo'shiq: .lyrics [nom] — Misol: .lyrics Bahor keldi",
    ".roulette": "🎰 Ruletka: .roulette — O'yin!",
    ".roleplay": "🎭 Rol: .roleplay [xarakter] — Misol: .roleplay hakim",
    ".read":     "📄 Fayl: .read — Javobdagi faylni o'qiydi",
    ".upload":   "📤 Yuklash: .upload — Faylni Telegraph ga yuklaydi",
    ".telegraph":"📝 Telegraph: .telegraph [sarlavha] [matn]",
    ".gender":   "👤 Jins: .gender [ism] — Misol: .gender Dilnoza",
    ".shortlink":"🔗 Link: .shortlink [url] — Misol: .shortlink https://google.com",
    ".ok":       "✅ Media saqlash: javobga .ok yozing",
}

HELP_TEXT = """📋 USERBOT BUYRUQLAR RO'YXATI

🤖 AI
  .ai [savol] — Claude bilan gaplashing
  .grok [savol] — Grok bilan gaplashing

🌐 Tarjima va Ovoz
  .tr [til] [matn] — Tarjima (en, ru, uz, ar...)
  .tts [matn] — Matnni ovozga aylantir

🎭 Animatsiya
  .co [matn] — Animatsiya effekti
  .love — Sevgi animatsiyasi

📥 Media
  .yt [havola] — YouTube video/audio
  .tt [havola] — TikTok video
  .ok — Javobdagi mediani saqlash

🌍 Ma'lumot
  .weather [shahar] — Ob-havo
  .currency [kod] — Valyuta kursi
  .lyrics [nom] — Qo'shiq matni
  .gender [ism] — Jins taxmini

🎮 O'yin va Ijod
  .q — Hikmatli gap
  .meme — Random meme
  .anime — Anime rasm
  .roulette — Ruletka o'yini
  .roleplay [xarakter] — Rol o'ynash
  .baza [so'z] — Ma'lumotlar bazasi

🔧 Vositalar
  .clock — Profilga soat qo'shish
  .shortlink [url] — URL qisqartirish
  .telegraph — Telegraph post
  .read — Faylni o'qish
  .upload — Telegraph ga yuklash
  .ping — Bot holati

Yordam: har bir buyruqni xato yozsangiz, to'g'ri foydalanishni ko'rsataman."""


def find_closest_command(text: str):
    """Find the closest valid command if user typed wrong one."""
    t = text.split()[0].lower() if text else ""
    if not t.startswith("."):
        return None
    # Exact match
    if t in VALID_COMMANDS:
        return t
    # Partial prefix match
    matches = [c for c in VALID_COMMANDS if c.startswith(t) or t.startswith(c[:3])]
    return matches[0] if len(matches) == 1 else None


@router.business_message()
async def handle_business_message(message: types.Message, bot: Bot):
    conn_id = message.business_connection_id
    if not conn_id:
        return

    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else 0
    conn = get_conn_settings(conn_id)

    # ── APPROVAL CHECK ──────────────────────────────────────
    if not conn.get("is_approved"):
        # Silently ignore — admin hasn't approved yet
        return

    if not conn.get("is_enabled") or not conn.get("can_reply", True):
        return

    text = message.text.strip() if message.text else ""

    # ── OWNER MESSAGES ──────────────────────────────────────
    if conn.get("user_id") and user_id == conn["user_id"]:
        # Owner saved media with .ok
        if text.lower() == ".ok" and message.reply_to_message:
            success = await media_service.save_temporary_media(bot, message, conn["user_id"])
            reply = "✅ Media saqlandi!" if success else "❌ Media yuklab bo'lmadi."
            await message.reply(reply, business_connection_id=conn_id)
            return

        # Owner .help — show userbot commands
        if text.lower() == ".help":
            await bot.send_message(
                chat_id=chat_id,
                text=HELP_TEXT,
                business_connection_id=conn_id,
                parse_mode=None
            )
            return

        # Owner typed a .command — check if valid, give help if wrong
        if text.startswith(".") and len(text) > 1:
            cmd_word = text.split()[0].lower()
            if cmd_word not in VALID_COMMANDS:
                closest = find_closest_command(cmd_word)
                if closest:
                    help_hint = COMMAND_HELP.get(closest, "")
                    await bot.send_message(
                        chat_id=chat_id,
                        text=(
                            f"❓ '{cmd_word}' buyrug'i topilmadi.\n\n"
                            f"Yaqin buyruq: {closest}\n"
                            f"{help_hint}\n\n"
                            f"Barcha buyruqlar: .help"
                        ),
                        business_connection_id=conn_id,
                        parse_mode=None
                    )
                else:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=f"❓ '{cmd_word}' noma'lum buyruq.\n\nBarcha buyruqlar ro'yxati: .help",
                        business_connection_id=conn_id,
                        parse_mode=None
                    )
                return
            else:
                # Valid command -> Check if it's an animation
                anim_name = cmd_word.replace(".", "")
                from services.animations_service import run_aiogram_animation, ANIMATIONS
                if anim_name in ANIMATIONS:
                    # Run animation using bot.send_message & bot.edit_message_text
                    import asyncio
                    asyncio.create_task(run_aiogram_animation(bot, chat_id, anim_name, conn_id=conn_id))
                    return
                elif cmd_word == ".ping":
                    import time
                    start = time.time()
                    msg = await bot.send_message(chat_id=chat_id, text="✅ <b>Ping: Tekshirilmoqda...</b>", business_connection_id=conn_id, parse_mode='HTML')
                    end = time.time()
                    ms = round((end - start) * 1000)
                    await bot.edit_message_text(chat_id=chat_id, message_id=msg.message_id, text=f"✅ <b>Ping: {ms} ms</b>", business_connection_id=conn_id, parse_mode='HTML')
                    return
                # If it's a valid command but not implemented in aiogram yet (like .weather), just say it's coming
                elif cmd_word not in [".help", ".ok"]:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=f"⏳ '{cmd_word}' buyrug'i tez orada Business rejimda ishga tushadi!",
                        business_connection_id=conn_id,
                        parse_mode=None
                    )
                    return

        # Owner's normal message → record as assistant, don't reply
        if message.text:
            add_message(chat_id, "assistant", message.text)
        return

    # ── CUSTOMER MESSAGE — AUTO REPLY ────────────────────────
    # Typing indicator
    try:
        await bot.send_chat_action(
            chat_id=chat_id,
            action=ChatAction.TYPING,
            business_connection_id=conn_id
        )
    except Exception as e:
        logger.warning(f"Typing action failed: {e}")

    # Build content
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
        gemini_contents = ["Kechirasiz, bu turdagi xabarni qo'llab-quvvatlamayman."]
        log_content = "[Qo'llab-quvvatlanmaydigan media]"

    # History
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

    # System prompt — use real username (not "Noma'lum")
    owner_handle = conn.get("username") or conn.get("first_name") or "akkount egasi"
    if conn.get("custom_system_prompt"):
        sys_prompt = conn["custom_system_prompt"]
    else:
        sys_prompt = (
            f"Sen {owner_handle} ning shaxsiy yordamchisisan. "
            f"Vazifang: kelgan xabarlarga o'zbek tilida javob berish. "
            f"Qoidalar: faqat o'zbek tilida yoz, o'zingni 'shaxsiy yordamchiman' deb tanishtir, "
            f"hech qachon Anthropic, Claude yoki AI ekanligingni aytma. "
            f"Javoblar qisqa va tabiiy bo'lsin."
        )

    selected_model = conn.get("model", "claude")

    try:
        reply_text = await claude_service.generate_response(
            contents=final_contents,
            system_prompt=sys_prompt,
            model=selected_model
        )
    except Exception as e:
        logger.error(f"AI error: {e}", exc_info=True)
        reply_text = "Kechirasiz, vaqtinchalik xatolik yuz berdi. Birozdan so'ng qayta yozing."

    add_message(chat_id, "assistant", reply_text)

    try:
        await bot.send_message(
            chat_id=chat_id,
            text=reply_text,
            business_connection_id=conn_id,
            parse_mode=None
        )
        logger.info(f"Business reply sent to {chat_id} via conn={conn_id}")
    except Exception as e:
        logger.error(f"Failed to send business reply: {e}", exc_info=True)


@router.edited_business_message()
async def handle_edited_business_message(message: types.Message):
    logger.info(f"Edited business message: conn_id={message.business_connection_id}")


@router.deleted_business_messages()
async def handle_deleted_business_messages(event: types.BusinessMessagesDeleted):
    logger.info(f"Deleted messages: conn_id={event.business_connection_id}, ids={event.message_ids}")
