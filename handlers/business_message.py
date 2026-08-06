import asyncio
import functools
import logging
from aiogram import Router, Bot, types
from aiogram.enums import ChatAction

from services.claude_service import claude_service
from services.media_service import media_service
from services import userbot_aiogram as ua
from services.animations_service import run_aiogram_animation, ANIMATIONS
from storage import get_conn_settings, add_message, get_history
from config import settings

logger = logging.getLogger(__name__)
router = Router()

# All valid userbot commands (for correction suggestions)
VALID_COMMANDS = [
    ".help", ".ping", ".ok",
    # AI
    ".ai", ".grok",
    # Tarjima / Ovoz
    ".tr", ".tts", ".t2s",
    # Animatsiya
    ".love", ".co", ".fun", ".komandalar",
    # Media / Ma'lumot
    ".yt", ".weather", ".q", ".r", ".meme", ".rmeme",
    ".anime", ".ra", ".aq", ".animequote", ".art",
    ".currency", ".kurs", ".lyrics", ".gender", ".shortlink", ".shlink",
    ".telegraph",
    # O'yin / Rol
    ".roulette", ".ro", ".me", ".do", ".try", ".todo",
    # Akkunt / Server
    ".acc", ".status", ".getid",
    # Timer
    ".time", ".settime",
    # Fayllar
    ".rf", ".read", ".upload",
    ".catbox", ".envs", ".kappa", ".oxo", ".0x0", ".x0", ".tmpfiles", ".pomf", ".bash",
    # Profil soati
    ".soat", ".soatbio",
    # Auto
    ".auto", ".stopauto",
]

COMMAND_HELP = {
    ".help":       "📋 Buyruqlar ro'yxati: shunchaki .help yozing.",
    ".ping":       "🏓 Ping: .ping — bot javob beradi.",
    ".ai":         "🤖 AI: .ai [savol] — Misol: .ai Toshkent qayerda?",
    ".grok":       "🌌 Grok: .grok [savol] — Misol: .grok kelajak haqida ayt",
    ".tr":         "🌐 Tarjima: .tr [til] [matn] — Misol: .tr en Salom dunyo",
    ".tts":        "🗣 Ovoz: .tts [matn] — Misol: .tts Assalomu alaykum",
    ".co":         "💫 Buyruqlar/Animatsiyalar: .co",
    ".love":       "❤️ Love: .love",
    ".yt":         "▶️ YouTube: .yt [qidiruv] — Misol: .yt O'zbekiston",
    ".weather":    "⛅ Ob-havo: .weather [shahar] — Misol: .weather Samarqand",
    ".q":          "💬 Quote: .q — xabarga reply qilib stiker yasash",
    ".r":          "🗨 Stiker: .r [matn] — xabarga reply qilib stiker yasash",
    ".meme":       "😂 Meme: .meme — Random meme",
    ".rmeme":      "😂 Meme: .rmeme — Random meme",
    ".anime":      "🎌 Anime: .anime — Random anime tavsiyasi",
    ".aq":         "🍿 Anime sitata: .aq [anime]",
    ".art":        "🖼 Anime surat: .art",
    ".currency":   "💱 Valyuta: .currency — Markaziy bank kurslari",
    ".lyrics":     "🎵 Qo'shiq: .lyrics [nom] — Misol: .lyrics Bahor keldi",
    ".roulette":   "🎰 Ruletka: .ro / .roulette — O'yin!",
    ".me":         "🌀 RolePlay: .me [harakat]",
    ".do":         "🌀 RolePlay: .do [voqea]",
    ".try":        "🌀 RolePlay: .try [harakat]",
    ".todo":       "🌀 RolePlay: .todo [fraza] [harakat]",
    ".acc":        "👤 Akkunt: .acc [id] — akkunt haqida ma'lumot",
    ".status":     "🖥 Server holati: .status",
    ".getid":      "🔖 Emoji ID: .getid — premium emojiga reply qiling",
    ".time":       "🎄 Timer: .time — voqegacha qolgan vaqt",
    ".settime":    "⏱ Timer sozlash: .settime 01.01.2027 | Xabar",
    ".rf":         "📄 Fayl: .rf — faylga reply qilib o'qish",
    ".catbox":     "📤 Yuklash: .catbox — faylga reply qiling",
    ".soat":       "🕒 Soat: .soat on|off — Ismga soat qo'shish",
    ".soatbio":    "🕒 Bio soat: .soatbio on|off",
    ".auto":       "📣 Reklama: .auto @guruh 60 | Xabar",
    ".stopauto":   "🛑 To'xtatish: .stopauto @guruh",
    ".gender":     "👤 Jins: .gender [ism] — Misol: .gender Dilnoza",
    ".shortlink":  "🔗 Link: .shortlink [url] — Misol: .shortlink https://google.com",
    ".telegraph":  "📝 Telegraph: .telegraph Sarlavha | Matn",
    ".ok":         "✅ Media saqlash: javobga .ok yozing",
}

HELP_TEXT = """📋 USERBOT BUYRUQLAR RO'YXATI

🤖 AI
  .ai [savol] — DeepSeek AI bilan gaplashing
  .grok [savol] — Grok AI bilan gaplashing

🌐 Tarjima va Ovoz
  .tr [til] [matn] — Tarjima (en, ru, uz, ar...)
  .tts [matn] — Matnni ovozga aylantir

🎭 Animatsiya
  .love, .snow, .xd, .police, .kill ... — animatsiyalar (.co)
  .co — barcha buyruqlar ro'yxati

📥 Media
  .yt [qidiruv] — YouTube dan qidirish
  .ok — Javobdagi mediani saqlash
  .catbox, .envs, .kappa ... — faylni yuklash (reply qilib)
  .rf — faylni o'qish (reply qilib)
  .r [matn] — stiker yasash (reply qilib)
  .q — quote stiker (reply qilib)
  .rmeme — random meme
  .telegraph Sarlavha | Matn — maqola yaratish

🌍 Ma'lumot
  .weather [shahar] — Ob-havo
  .currency — Valyuta kursi
  .lyrics [nom] — Qo'shiq matni
  .gender [ism] — Jins taxmini
  .shortlink [url] — URL qisqartirish
  .acc — Akkunt ma'lumoti
  .status — Server holati
  .getid — Premium emoji ID

🎮 O'yin va Ijod
  .ro — Rus ruletkasi
  .me / .do / .try / .todo — RolePlay
  .anime — Random anime
  .aq — Anime sitata
  .art — Anime surat
  .time / .settime — Timer

🕒 Profil
  .soat on|off — Ismga soat
  .soatbio on|off — Bioga soat
  .ping — Bot holati

📣 Avtomatik
  .auto @guruh 60 | Xabar — auto-reklama
  .stopauto @guruh — to'xtatish

Yordam: har bir buyruqni xato yozsangiz, to'g'ri foydalanishni ko'rsataman."""


# ─────────────────────────────────────────────────────────────
# COMMAND DISPATCH  (buyruq -> handler)
# ─────────────────────────────────────────────────────────────

UPLOAD_SERVICES = {
    ".catbox": "catbox",
    ".upload": "catbox",
    ".envs": "envs",
    ".kappa": "kappa",
    ".oxo": "0x0",
    ".0x0": "0x0",
    ".x0": "x0",
    ".tmpfiles": "tmpfiles",
    ".pomf": "pomf",
    ".bash": "bash",
}

COMMAND_DISPATCH = {
    ".ai": ua.cmd_ai,
    ".grok": ua.cmd_grok,
    ".tr": ua.cmd_translate,
    ".tts": ua.cmd_tts,
    ".t2s": ua.cmd_tts,
    ".weather": ua.cmd_weather,
    ".currency": ua.cmd_currency,
    ".kurs": ua.cmd_currency,
    ".lyrics": ua.cmd_lyrics,
    ".shortlink": ua.cmd_shortlink,
    ".shlink": ua.cmd_shortlink,
    ".gender": ua.cmd_gender,
    ".telegraph": ua.cmd_telegraph,
    ".yt": ua.cmd_yt_search,
    ".anime": ua.cmd_random_anime,
    ".ra": ua.cmd_random_anime,
    ".aq": ua.cmd_anime_quote,
    ".animequote": ua.cmd_anime_quote,
    ".art": ua.cmd_anime_art,
    ".q": ua.cmd_quote,
    ".r": ua.cmd_spoof_quote,
    ".ro": ua.cmd_roulette,
    ".roulette": ua.cmd_roulette,
    ".me": ua.cmd_me,
    ".do": ua.cmd_do,
    ".try": ua.cmd_try,
    ".todo": ua.cmd_todo,
    ".acc": ua.cmd_acc,
    ".status": ua.cmd_status,
    ".getid": ua.cmd_getid,
    ".time": ua.cmd_time,
    ".settime": ua.cmd_settime,
    ".rf": ua.cmd_read_file,
    ".read": ua.cmd_read_file,
    ".meme": ua.cmd_random_meme,
    ".rmeme": ua.cmd_random_meme,
    ".soat": ua.cmd_soat,
    ".soatbio": ua.cmd_soatbio,
    ".auto": ua.cmd_auto,
    ".stopauto": ua.cmd_stopauto,
    ".fun": ua.cmd_fun_list,
    ".co": ua.cmd_fun_list,
    ".komandalar": ua.cmd_fun_list,
}

for _cmd, _svc in UPLOAD_SERVICES.items():
    COMMAND_DISPATCH[_cmd] = functools.partial(ua.cmd_upload, service=_svc)


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


async def handle_owner_command(bot: Bot, message: types.Message, conn_id: str, cmd_word: str, args: str):
    """Run a single userbot command from the owner. Returns True if it was a command."""
    # Special commands
    if cmd_word == ".help":
        await bot.send_message(
            chat_id=message.chat.id,
            text=HELP_TEXT,
            business_connection_id=conn_id,
            parse_mode=None
        )
        return True

    if cmd_word == ".ping":
        import time
        start = time.time()
        msg = await bot.send_message(chat_id=message.chat.id, text="✅ <b>Ping: Tekshirilmoqda...</b>", business_connection_id=conn_id, parse_mode='HTML')
        end = time.time()
        ms = round((end - start) * 1000)
        await bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=f"✅ <b>Ping: {ms} ms</b>", business_connection_id=conn_id, parse_mode='HTML')
        return True

    # Animations (e.g. .love, .snow, ...)
    anim_name = cmd_word.replace(".", "")
    if anim_name in ANIMATIONS:
        asyncio.create_task(run_aiogram_animation(bot, message.chat.id, anim_name, conn_id=conn_id))
        return True

    # Registered commands
    handler = COMMAND_DISPATCH.get(cmd_word)
    if handler:
        try:
            await handler(bot, message, conn_id, args)
        except Exception as e:
            logger.error(f"Command {cmd_word} error: {e}", exc_info=True)
            try:
                await bot.send_message(
                    chat_id=message.chat.id,
                    text=f"🚫 <b>'{cmd_word}' da xatolik yuz berdi:</b> <code>{e}</code>",
                    business_connection_id=conn_id,
                    parse_mode='HTML'
                )
            except Exception:
                pass
        return True

    return False


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

        # Owner typed a .command — dispatch it
        if text.startswith(".") and len(text) > 1:
            parts = text.split(maxsplit=1)
            cmd_word = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""

            if cmd_word in VALID_COMMANDS:
                await handle_owner_command(bot, message, conn_id, cmd_word, args)
            else:
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
