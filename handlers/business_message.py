import asyncio
import functools
import logging
import time
from datetime import datetime
from aiogram import Router, Bot, types
from aiogram.enums import ChatAction

from services.claude_service import claude_service
from services.media_service import media_service
from services import userbot_aiogram as ua
from services.animations_service import run_aiogram_animation, ANIMATIONS
from storage import (
    get_conn_settings, set_conn_setting, add_message, get_history, get_chat_model,
    ADMIN_ID, get_greeting_date, set_greeting_date,
)
from config import settings

logger = logging.getLogger(__name__)
router = Router()

# Per-chat AI cooldown (chat_id -> last reply timestamp) to prevent AI spam
# without blocking owner commands. Commands always work; only the auto-reply
# is throttled.
_last_ai_reply: dict = {}

# All valid userbot commands (for correction suggestions)
VALID_COMMANDS = [
    ".help", ".ping", ".ok",
    # AI
    ".ai", ".grok", ".gpt", ".model",
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

# Every defined animation is a valid command (e.g. .love, .snow, .xd, ...)
VALID_COMMANDS.extend(f".{name}" for name in ANIMATIONS)

COMMAND_HELP = {
    ".help":       "📋 Buyruqlar ro'yxati: shunchaki .help yozing.",
    ".ping":       "🏓 Ping: .ping — bot javob beradi.",
    ".ai":         "🤖 AI: .ai [savol] — Misol: .ai Toshkent qayerda?",
    ".grok":       "🌌 Grok: .grok [savol] — Misol: .grok kelajak haqida ayt",
    ".gpt":        "🤖 GPT: .gpt [savol] — Misol: .gpt massiv nima?",
    ".model":      "🎛 Model: .model claude|grok|gpt|deepseek — Bu chat uchun AI modelni pinlash",
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
  .gpt [savol] — GPT AI bilan gaplashing
  .model claude|grok|gpt|deepseek — Bu chat uchun AI modelni pinlash

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
    ".gpt": ua.cmd_gpt,
    ".model": ua.cmd_model,
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


def _is_owner_message(message: types.Message, conn: dict) -> bool:
    """Only the admin is treated as the account owner — nobody else is served."""
    uid = message.from_user.id if message.from_user else None
    return uid == ADMIN_ID


# Dedup: the same message can arrive as BOTH a "message" and a "business_message"
# update. Without this, .help and other commands get sent multiple times.
_last_cmd: dict = {}


def _dedupe_command(chat_id: int, user_id: int, text: str) -> bool:
    """True if this exact command was already handled in the last 3 seconds."""
    key = (chat_id, user_id, text)
    now = time.time()
    if key in _last_cmd and now - _last_cmd[key] < 3.0:
        return True
    _last_cmd[key] = now
    return False


async def _delete_owner_command(bot: Bot, conn_id: str, message: types.Message):
    """Delete the owner's dot-command message (best-effort).

    Requires the 'can_delete_all_messages' business bot right, granted when the
    user connected the bot. If the right is missing, the command still runs —
    the original message just stays visible.
    """
    if not conn_id:
        return
    try:
        await bot.delete_business_messages(
            business_connection_id=conn_id,
            message_ids=[message.message_id]
        )
    except Exception as e:
        logger.debug(f"Could not delete owner command message: {e}")


async def _send_text_fb(bot: Bot, chat_id: int, text: str, conn_id: str, parse_mode=None):
    """Send a message, preferring the business connection, falling back to a normal message."""
    try:
        await bot.send_message(chat_id=chat_id, text=text, business_connection_id=conn_id, parse_mode=parse_mode)
    except Exception:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)


async def _generate_auto_reply(contents, sys_prompt, preferred_model):
    """Generate a customer auto-reply. Tries the pinned model first, then falls
    back to claude → gpt → grok so the bot always answers even when a single AI
    service is down or slow (the previous version went silent on a timeout)."""
    chain = []
    preferred = (preferred_model or "claude").lower()
    first = preferred if preferred in ("claude", "gpt", "grok", "deepseek") else "claude"
    chain.append(first)
    for m in ("claude", "gpt", "grok"):
        if m != first:
            chain.append(m)

    for model in chain:
        try:
            if model == "deepseek":
                text_parts = [p for p in contents if isinstance(p, str)]
                full_query = "\n".join(text_parts) if text_parts else "Salom!"
                reply = await asyncio.wait_for(
                    ua.ask_deepseek(full_query, sys_prompt), timeout=30
                )
            else:
                reply = await asyncio.wait_for(
                    claude_service.generate_response(
                        contents=contents,
                        system_prompt=sys_prompt,
                        model=model,
                        retries=1,
                        timeout=15,
                    ),
                    timeout=25,
                )
            if reply and reply.strip():
                logger.info(f"Auto-reply answered with model={model}")
                return reply
        except asyncio.TimeoutError:
            logger.warning(f"Auto-reply timeout for model={model}")
        except Exception as e:
            logger.warning(f"Auto-reply failed for model={model}: {e}")
    return None


async def handle_owner_command(bot: Bot, message: types.Message, conn_id: str, cmd_word: str, args: str):
    """Run a single userbot command from the owner. Returns True if it was a command."""
    logger.info(f"Owner command: {cmd_word} in chat {message.chat.id} (conn={conn_id})")
    # Special commands
    if cmd_word == ".help":
        await _send_text_fb(bot, message.chat.id, HELP_TEXT, conn_id)
        return True

    if cmd_word == ".ping":
        import time
        start = time.time()
        msg = None
        try:
            msg = await bot.send_message(chat_id=message.chat.id, text="✅ <b>Ping: Tekshirilmoqda...</b>", business_connection_id=conn_id, parse_mode='HTML')
            use_conn = conn_id
        except Exception:
            msg = await bot.send_message(chat_id=message.chat.id, text="✅ <b>Ping: Tekshirilmoqda...</b>", parse_mode='HTML')
            use_conn = None
        end = time.time()
        ms = round((end - start) * 1000)
        try:
            await bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=f"✅ <b>Ping: {ms} ms</b>", business_connection_id=use_conn, parse_mode='HTML')
        except Exception:
            pass
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
            err_text = f"🚫 '{cmd_word}' da xatolik yuz berdi: {e}"
            try:
                await bot.send_message(
                    chat_id=message.chat.id,
                    text=err_text,
                    business_connection_id=conn_id,
                    parse_mode=None
                )
            except Exception:
                try:
                    await bot.send_message(
                        chat_id=message.chat.id,
                        text=err_text,
                        parse_mode=None
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

    uid = message.from_user.id if message.from_user else 0
    sender_bot = message.sender_business_bot.id if message.sender_business_bot else None
    logger.info(
        f"[BIZ-MSG] chat={message.chat.id} from={uid} conn={conn_id} "
        f"type={message.chat.type} sender_bot={sender_bot} "
        f"conn_user={conn.get('user_id')} text='{(message.text or message.caption or '')[:50]}'"
    )

    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else 0
    conn = get_conn_settings(conn_id)

    # The bot serves ONLY the admin's own business account. Any other connected
    # account is completely ignored — no auto-replies, no commands.
    #
    # NOTE: Render's filesystem is ephemeral, so database/*.json is wiped on
    # every redeploy. That erases the stored connection user_id, which would
    # drop every message (customer replies AND owner commands) after a deploy.
    # Owner commands are therefore decided by the SENDER, not the registry: an
    # unknown connection is assumed to be the admin's and re-registered.
    known_uid = conn.get("user_id")
    if known_uid is not None and known_uid != ADMIN_ID:
        logger.warning(
            f"Ignoring connection {conn_id}: conn_user_id={known_uid} != ADMIN_ID={ADMIN_ID}"
        )
        return

    text = message.text.strip() if message.text else ""
    raw_text = (message.text or message.caption or "").strip()

    # ── OWNER MESSAGES ──────────────────────────────────────
    # The owner's OWN messages must NEVER be auto-replied —
    # the AI only writes back when a customer writes TO the owner.
    # Owner commands ALWAYS work, even if the connection is not yet
    # approved/enabled (approval only gates the customer auto-reply).
    if _is_owner_message(message, conn):
        if known_uid != ADMIN_ID:
            logger.warning(
                f"Connection {conn_id} ownership unknown (post-redeploy wipe) — "
                f"re-registering it as the admin's own account."
            )
            set_conn_setting(
                conn_id,
                user_id=ADMIN_ID,
                is_enabled=True,
                is_approved=True,
            )
            conn = get_conn_settings(conn_id)
        # Owner saved media with .ok — fully SILENT in the source chat: the
        # command message is deleted and the content (media, voice, text, ...)
        # is sent privately to the admin. Nothing is shown where .ok was used.
        if text.lower() == ".ok":
            await _delete_owner_command(bot, conn_id, message)
            if message.reply_to_message:
                ok = await media_service.save_temporary_media(bot, message, ADMIN_ID)
                if not ok:
                    try:
                        await bot.send_message(
                            chat_id=ADMIN_ID,
                            text="❌ Mediani saqlashda xatolik yuz berdi.",
                            parse_mode=None
                        )
                    except Exception:
                        pass
            return

        # Owner typed a .command — dispatch it
        if text.startswith(".") and len(text) > 1:
            if _dedupe_command(chat_id, user_id, text):
                return
            parts = text.split(maxsplit=1)
            cmd_word = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""

            # Delete the owner's command message immediately, then run the command
            await _delete_owner_command(bot, conn_id, message)

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
    # No approval needed — the bot works immediately for the admin account.
    # can_reply is NOT checked here: if the business-connection send fails the
    # reply is re-sent as a normal bot message, so a reply always goes out.
    # An unknown connection (post-redeploy wipe) is treated as the admin's own.
    if known_uid != ADMIN_ID:
        logger.warning(
            f"Connection {conn_id} ownership unknown (post-redeploy wipe) — "
            f"assuming admin's own account and re-registering it."
        )
        set_conn_setting(
            conn_id,
            user_id=ADMIN_ID,
            is_enabled=True,
            is_approved=True,
        )
        conn = get_conn_settings(conn_id)

    if not conn.get("is_enabled"):
        return

    # Never auto-reply to messages without a known sender (channel posts etc.)
    if user_id == 0:
        logger.info(f"Skipping sender-less message in chat {chat_id} (no AI reply)")
        return

    # Never auto-reply to commands / dot-prefixed messages
    if raw_text.startswith("."):
        logger.info(f"Skipping dot message from {user_id} in chat {chat_id} (no AI reply)")
        return

    # Per-chat AI cooldown — prevents the bot from replying to rapid spam
    # but never blocks commands (owner branch handled above).
    now = time.time()
    if chat_id in _last_ai_reply and now - _last_ai_reply[chat_id] < settings.rate_limit_seconds:
        logger.info(f"AI cooldown active in chat {chat_id} — skipping auto reply")
        return

    # Greet only once per day, then keep the conversation going naturally.
    today = datetime.now().strftime("%Y-%m-%d")
    first_msg_today = get_greeting_date(chat_id) != today
    if first_msg_today:
        set_greeting_date(chat_id, today)

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

    # Once-a-day greeting: greet the customer on their first message of the day,
    # then simply continue the conversation without re-greeting.
    if first_msg_today:
        sys_prompt += (
            f"\n\nQo'shimcha: bugun bu mijoz bilan suhbat endi boshlandi. "
            f"Javobni qisqagina salom (masalan 'Assalomu alaykum!') bilan boshlab, "
            f"so'ng murojaatiga javob ber."
        )
    else:
        sys_prompt += (
            f"\n\nQo'shimcha: bugun bu chatda allaqachon salomlashilgan. "
            f"QAYTA salom berma! To'g'ridan-to'g'ri suhbatni davom ettir — "
            f"xuddi davom etayotgan muloqotdek javob ber."
        )

    # Model: a chat pinned via .ai/.grok/.model keeps that model until switched.
    selected_model = get_chat_model(conn_id, chat_id) or conn.get("model", "claude")

    # Multi-model fallback chain — the bot never stays silent when one AI is down.
    reply_text = await _generate_auto_reply(final_contents, sys_prompt, selected_model)

    _last_ai_reply[chat_id] = time.time()

    if reply_text is None:
        # Every AI service was down — send a short friendly note so the customer
        # is never left without an answer.
        reply_text = "Kechirasiz, hozircha bandman. Birozdan so'ng qayta yozing."

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
        try:
            await bot.send_message(chat_id=chat_id, text=reply_text, parse_mode=None)
            logger.info(f"Reply sent to {chat_id} via normal bot message")
        except Exception as e2:
            logger.error(f"Failed to send normal reply: {e2}", exc_info=True)


@router.edited_business_message()
async def handle_edited_business_message(message: types.Message):
    logger.info(f"Edited business message: conn_id={message.business_connection_id}")


@router.deleted_business_messages()
async def handle_deleted_business_messages(event: types.BusinessMessagesDeleted):
    logger.info(f"Deleted messages: conn_id={event.business_connection_id}, ids={event.message_ids}")
