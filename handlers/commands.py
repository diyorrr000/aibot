import logging
from aiogram import Router, types, Bot, F
from aiogram.enums import ChatAction
from aiogram.filters import Command, CommandObject

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from storage import (
    ADMIN_ID,
    get_conn_settings,
    set_conn_setting,
    clear_history,
    connection_settings,
    add_message,
    get_history,
    is_clock_enabled,
    set_clock_enabled,
)
from config import settings
from services.claude_service import claude_service
from services.media_service import media_service

logger = logging.getLogger(__name__)
router = Router()

MODEL_NAMES = {
    "claude": "🧠 Claude Haiku 4.5",
    "grok":   "🌌 Grok 4.3",
    "gpt":    "🤖 GPT 4o"
}

# ─────────────────────────────────────────────────────────
# USERBOT BUYRUQLAR RO'YXATI (.help uchun)
# ─────────────────────────────────────────────────────────
USERBOT_COMMANDS = {
    ".help":       ("📋 Yordam", "Barcha buyruqlar ro'yxatini ko'rsatadi."),
    ".ping":       ("🏓 Ping", "Botning ishlash holatini tekshiradi."),
    ".ai":         ("🤖 AI savol", "DeepSeek AI. Misol: .ai Uzbekiston poytaxti qaysi?"),
    ".grok":       ("🌌 Grok AI", "Grok modeli. Misol: .grok kelajak haqida ayt"),
    ".gpt":        ("🤖 GPT AI", "GPT modeli. Misol: .gpt Python nima?"),
    ".model":      ("🎛 AI Model", "Bu chat uchun model pinlash. Misol: .model claude|grok|gpt|deepseek"),
    ".tr":         ("🌐 Tarjima", "Xabarni tarjima qiladi. Misol: .tr ru Hello world"),
    ".tts":        ("🗣 Ovozli xabar", "Matnni ovozga aylantiradi. Misol: .tts Salom"),
    ".co":         ("💫 Buyruqlar", "Barcha animatsiya va modullar ro'yxati."),
    ".love":       ("❤️ Love animatsiya", "Sevgi animatsiyasi. Misol: .love"),
    ".weather":    ("⛅ Ob-havo", "Shahar ob-havosi. Misol: .weather Toshkent"),
    ".yt":         ("▶️ YouTube", "YouTube dan qidirish. Misol: .yt O'zbekiston"),
    ".q":          ("💬 Quote", "Xabarga reply qilib quote stiker yasash."),
    ".r":          ("🗨 Stiker", "Xabarga reply qilib stiker yasash. Misol: .r Salom"),
    ".meme":       ("😂 Meme", "Random meme yuboradi."),
    ".anime":      ("🎌 Anime", "Random anime tavsiyasi."),
    ".aq":         ("🍿 Anime sitata", "Anime sitata. Misol: .aq Naruto"),
    ".art":        ("🖼 Anime surat", "Anime surat yuboradi."),
    ".currency":   ("💱 Valyuta", "Markaziy bank kurslari."),
    ".lyrics":     ("🎵 Qo'shiq matni", "Qo'shiq so'zlari. Misol: .lyrics Bahor keldi"),
    ".roulette":   ("🎰 Ruletka", "Rus ruletkasi o'yini."),
    ".me":         ("🌀 RolePlay .me", "Birinchi shaxs nomidan. Misol: .me choy ichdi"),
    ".do":         ("🌀 RolePlay .do", "Atrofdagi voqea. Misol: .do Quyosh chiqdi"),
    ".try":        ("🌀 RolePlay .try", "Omadingizni sinash. Misol: .try moshina"),
    ".todo":       ("🌀 RolePlay .todo", "Fraza va harakat. Misol: .todo Salom. qo'l silkitib"),
    ".acc":        ("👤 Akkunt", "Akkunt haqida ma'lumot. Misol: .acc 123456789"),
    ".status":     ("🖥 Server holati", "Server xotira/CPU holati."),
    ".getid":      ("🔖 Emoji ID", "Premium emoji ID olish (reply qiling)."),
    ".time":       ("🎄 Timer", "Voqegacha qolgan vaqtni ko'rsatadi."),
    ".settime":    ("⏱ Timer sozlash", ".settime 01.01.2027 | Xabar"),
    ".rf":         ("📄 Fayl o'qish", "Faylni o'qiydi. Misol: .rf (reply)"),
    ".catbox":     ("📤 Yuklash", "Faylni yuklash. Misol: .catbox (reply)"),
    ".soat":       ("🕒 Ism soati", "Ismga soat qo'shish. Misol: .soat on|off"),
    ".soatbio":    ("🕒 Bio soati", "Bioga soat qo'shish. Misol: .soatbio on|off"),
    ".auto":       ("📣 Auto-reklama", ".auto @guruh 60 | Xabar"),
    ".stopauto":   ("🛑 Reklamani to'xtatish", ".stopauto @guruh"),
    ".telegraph":  ("📝 Telegraph", "Telegraph ga post. Misol: .telegraph Sarlavha | Matn"),
    ".gender":     ("👤 Jins aniqlash", "Ism orqali jins. Misol: .gender Sardor"),
    ".shortlink":  ("🔗 Qisqa havola", "URL qisqartiradi. Misol: .shortlink https://..."),
    ".ok":         ("✅ Media saqlash", "Javobdagi mediani shaxsiy chatga saqlaydi."),
}


def find_user_connection(user_id: int):
    for conn_id, s in connection_settings.items():
        if s.get("user_id") == user_id:
            return conn_id, s
    return None, None


# ─────────────────────────────────────────────────────────
# SETTINGS PANEL TEXT
# ─────────────────────────────────────────────────────────
def build_settings_panel(user_id: int):
    is_admin = (user_id == ADMIN_ID)
    clock_st = "🟢 YOQILGAN (Asia/Tashkent)" if is_clock_enabled() else "🔴 O'CHIRILGAN"

    msg = "⚙️ BOT BOSHQARUV PANELI\n\n"
    msg += f"🕒 Profil Soati: {clock_st}\n"
    msg += f"📊 Ulangan akkuntlar: {len(connection_settings)} ta\n\n"

    if not connection_settings:
        msg += "ℹ️ Hozircha ulangan Business hisob yo'q.\n"
        msg += "Ulanish uchun: Telegram Settings → Telegram Business → Chat Bots → botni qo'shing.\n"
        msg += "Ulangandan keyin admin TASDIQLASHI kerak.\n"
    else:
        msg += "📋 Ulangan Business Hisoblar:\n\n"
        for conn_id, s in connection_settings.items():
            if is_admin or s.get("user_id") == user_id:
                auto_st = "🟢 Yoqilgan" if s.get("is_enabled") else "🔴 O'chirilgan"
                approved_st = "✅ Tasdiqlangan" if s.get("is_approved") else "⏳ Admin tasdig'i kutilmoqda"
                curr_model = s.get("model", "claude")
                model_name_str = MODEL_NAMES.get(curr_model, curr_model)
                username = s.get("username") or "Noma'lum"
                msg += (
                    f"👤 Hisob: {username}\n"
                    f"🔐 Holat: {approved_st}\n"
                    f"🤖 AI Model: {model_name_str}\n"
                    f"⚡ Avto-Javob: {auto_st}\n\n"
                )

    if is_admin:
        msg += "📌 Admin buyruqlari: /approve <conn_id> | /disapprove <conn_id> | /connections\n"

    msg += "\n.help — userbot buyruqlar ro'yxati"
    return msg


# ─────────────────────────────────────────────────────────
# SETTINGS KEYBOARD (faqat zarur tugmalar)
# ─────────────────────────────────────────────────────────
def get_settings_keyboard(user_id: int):
    keyboard = []
    is_admin = (user_id == ADMIN_ID)

    # Clock Toggle
    clock_status = "🟢 YOQILGAN" if is_clock_enabled() else "🔴 O'CHIRILGAN"
    keyboard.append([
        InlineKeyboardButton(text=f"🕒 Profil Soati: {clock_status}", callback_data="toggle_clock")
    ])

    # Business account controls
    for conn_id, s in connection_settings.items():
        if is_admin or s.get("user_id") == user_id:
            curr_m = s.get("model", "claude")
            auto_enabled = s.get("is_enabled", True)
            username = s.get("username", "Hisob")

            # AI Model selection row
            claude_label = "✅ 🧠 Claude 4.5" if curr_m == "claude" else "🧠 Claude 4.5"
            grok_label   = "✅ 🌌 Grok 4.3"   if curr_m == "grok"   else "🌌 Grok 4.3"
            gpt_label    = "✅ 🤖 GPT 4o"     if curr_m == "gpt"    else "🤖 GPT 4o"
            keyboard.append([
                InlineKeyboardButton(text=claude_label, callback_data=f"set_model:{conn_id}:claude"),
                InlineKeyboardButton(text=grok_label,   callback_data=f"set_model:{conn_id}:grok"),
                InlineKeyboardButton(text=gpt_label,    callback_data=f"set_model:{conn_id}:gpt"),
            ])

            # Auto-reply toggle
            auto_btn_text = "⚡ Avto-Javob: 🟢" if auto_enabled else "⚡ Avto-Javob: 🔴"
            keyboard.append([
                InlineKeyboardButton(text=auto_btn_text, callback_data=f"toggle_auto:{conn_id}")
            ])

            # Approval (admin only)
            if is_admin:
                is_approved = s.get("is_approved", False)
                apr_text = "✅ Tasdiqlangan" if is_approved else "⏳ Tasdiqlash"
                keyboard.append([
                    InlineKeyboardButton(text=apr_text, callback_data=f"approve_conn:{conn_id}"),
                    InlineKeyboardButton(text="❌ Rad etish", callback_data=f"disapprove_conn:{conn_id}"),
                ])

    # Utility row
    keyboard.append([
        InlineKeyboardButton(text="🗑 Tarixni tozalash", callback_data="clear_chat_history"),
        InlineKeyboardButton(text="🔄 Yangilash", callback_data="refresh_panel"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ─────────────────────────────────────────────────────────
# APPLY MODEL CHANGE
# ─────────────────────────────────────────────────────────
async def apply_model_change(bot: Bot, conn_id: str, target_model: str):
    set_conn_setting(conn_id, model=target_model)
    conn = get_conn_settings(conn_id)
    user_id = conn.get("user_id")
    if user_id:
        model_title = MODEL_NAMES.get(target_model, target_model)
        try:
            await bot.send_message(
                chat_id=user_id,
                text=(
                    f"🤖 AI Model yangilandi!\n\n"
                    f"Joriy Model: {model_title}\n"
                    f"Business xabarlaringizga endi {model_title} orqali javob beriladi."
                ),
                parse_mode=None
            )
        except Exception as e:
            logger.warning(f"Model change notify failed for {user_id}: {e}")


# ─────────────────────────────────────────────────────────
# COMMANDS
# ─────────────────────────────────────────────────────────
@router.message(Command("start"))
@router.message(Command("admin"))
@router.message(Command("settings"))
@router.message(Command("panel"))
async def cmd_settings_panel(message: types.Message):
    user_id = message.from_user.id
    await message.answer(build_settings_panel(user_id), parse_mode=None, reply_markup=get_settings_keyboard(user_id))


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = "📋 USERBOT BUYRUQLAR RO'YXATI\n\n"
    for cmd, (title, desc) in USERBOT_COMMANDS.items():
        help_text += f"{title}\n  Buyruq: {cmd}\n  {desc}\n\n"
    help_text += "Har qanday buyruqni yozishda xato bo'lsa, bot to'g'ri foydalanishni ko'rsatadi."
    await message.answer(help_text, parse_mode=None)


@router.message(Command("connections"))
async def cmd_connections(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    if not connection_settings:
        await message.answer("ℹ️ Hozircha ulangan hisob yo'q.", parse_mode=None)
        return
    text = "📋 Barcha ulangan hisoblar:\n\n"
    for conn_id, s in connection_settings.items():
        status = "✅" if s.get("is_approved") else "⏳"
        text += f"{status} {s.get('username', '?')} — ID: {conn_id}\n"
    await message.answer(text, parse_mode=None)


@router.message(Command("approve"))
async def cmd_approve(message: types.Message, command: CommandObject, bot: Bot):
    if message.from_user.id != ADMIN_ID:
        return
    conn_id = command.args
    if not conn_id or conn_id not in connection_settings:
        await message.answer("⚠️ Foydalanish: /approve <connection_id>\nID ni /connections orqali ko'ring.", parse_mode=None)
        return
    set_conn_setting(conn_id, is_approved=True, is_enabled=True)
    conn = get_conn_settings(conn_id)
    await message.answer(f"✅ {conn.get('username', conn_id)} tasdiqlandi va bot faollashdi!", parse_mode=None)
    if conn.get("user_id"):
        try:
            await bot.send_message(
                chat_id=conn["user_id"],
                text=(
                    "🎉 Botingiz admin tomonidan tasdiqlandi!\n\n"
                    "Endi Telegram Business xabarlaringizga avtomatik javob beriladi.\n"
                    "Buyruqlar ro'yxati uchun .help yozing."
                ),
                parse_mode=None
            )
        except Exception as e:
            logger.warning(f"Approve notify failed: {e}")


@router.message(Command("disapprove"))
async def cmd_disapprove(message: types.Message, command: CommandObject, bot: Bot):
    if message.from_user.id != ADMIN_ID:
        return
    conn_id = command.args
    if not conn_id or conn_id not in connection_settings:
        await message.answer("⚠️ Foydalanish: /disapprove <connection_id>", parse_mode=None)
        return
    set_conn_setting(conn_id, is_approved=False, is_enabled=False)
    conn = get_conn_settings(conn_id)
    await message.answer(f"❌ {conn.get('username', conn_id)} rad etildi.", parse_mode=None)
    if conn.get("user_id"):
        try:
            await bot.send_message(
                chat_id=conn["user_id"],
                text="⚠️ Business ulanishingiz admin tomonidan to'xtatildi.",
                parse_mode=None
            )
        except Exception as e:
            logger.warning(f"Disapprove notify failed: {e}")


@router.message(Command("reset"))
async def cmd_reset(message: types.Message):
    clear_history(message.chat.id)
    await message.answer("✅ Suhbat tarixi tozalandi!", parse_mode=None)


# ─────────────────────────────────────────────────────────
# CALLBACK HANDLERS
# ─────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("set_model:"))
async def cb_set_model(callback: types.CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    parts = callback.data.split(":")
    if len(parts) == 3:
        conn_id, target_model = parts[1], parts[2]
        conn = get_conn_settings(conn_id)
        if user_id != ADMIN_ID and conn.get("user_id") != user_id:
            await callback.answer("⚠️ Sizga ruxsat berilmagan!", show_alert=True)
            return
        await apply_model_change(bot, conn_id, target_model)
        model_title = MODEL_NAMES.get(target_model, target_model)
        await callback.answer(f"AI Model {model_title} ga o'zgartirildi!", show_alert=True)
        try:
            await callback.message.edit_text(build_settings_panel(user_id), parse_mode=None, reply_markup=get_settings_keyboard(user_id))
        except Exception:
            pass


@router.callback_query(F.data.startswith("toggle_auto:"))
async def cb_toggle_auto(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    parts = callback.data.split(":")
    if len(parts) == 2:
        conn_id = parts[1]
        conn = get_conn_settings(conn_id)
        if user_id != ADMIN_ID and conn.get("user_id") != user_id:
            await callback.answer("⚠️ Sizga ruxsat berilmagan!", show_alert=True)
            return
        new_enabled = not conn.get("is_enabled", True)
        set_conn_setting(conn_id, is_enabled=new_enabled)
        status_text = "YOQILDI 🟢" if new_enabled else "O'CHIRILDI 🔴"
        await callback.answer(f"Avto-Javob {status_text}!", show_alert=True)
        try:
            await callback.message.edit_text(build_settings_panel(user_id), parse_mode=None, reply_markup=get_settings_keyboard(user_id))
        except Exception:
            pass


@router.callback_query(F.data.startswith("approve_conn:"))
async def cb_approve_conn(callback: types.CallbackQuery, bot: Bot):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Faqat admin uchun!", show_alert=True)
        return
    conn_id = callback.data.split(":")[1]
    if conn_id not in connection_settings:
        await callback.answer("Bunday ulanish topilmadi!", show_alert=True)
        return
    set_conn_setting(conn_id, is_approved=True, is_enabled=True)
    conn = get_conn_settings(conn_id)
    await callback.answer(f"✅ {conn.get('username', conn_id)} tasdiqlandi!", show_alert=True)
    if conn.get("user_id"):
        try:
            await bot.send_message(
                chat_id=conn["user_id"],
                text=(
                    "🎉 Botingiz admin tomonidan tasdiqlandi!\n\n"
                    "Endi Telegram Business xabarlaringizga avtomatik javob beriladi.\n"
                    "Buyruqlar ro'yxati uchun .help yozing."
                ),
                parse_mode=None
            )
        except Exception:
            pass
    try:
        await callback.message.edit_text(build_settings_panel(ADMIN_ID), parse_mode=None, reply_markup=get_settings_keyboard(ADMIN_ID))
    except Exception:
        pass


@router.callback_query(F.data.startswith("disapprove_conn:"))
async def cb_disapprove_conn(callback: types.CallbackQuery, bot: Bot):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Faqat admin uchun!", show_alert=True)
        return
    conn_id = callback.data.split(":")[1]
    if conn_id not in connection_settings:
        await callback.answer("Bunday ulanish topilmadi!", show_alert=True)
        return
    set_conn_setting(conn_id, is_approved=False, is_enabled=False)
    conn = get_conn_settings(conn_id)
    await callback.answer(f"❌ {conn.get('username', conn_id)} rad etildi.", show_alert=True)
    if conn.get("user_id"):
        try:
            await bot.send_message(
                chat_id=conn["user_id"],
                text="⚠️ Business ulanishingiz admin tomonidan to'xtatildi.",
                parse_mode=None
            )
        except Exception:
            pass
    try:
        await callback.message.edit_text(build_settings_panel(ADMIN_ID), parse_mode=None, reply_markup=get_settings_keyboard(ADMIN_ID))
    except Exception:
        pass


@router.callback_query(F.data == "toggle_clock")
async def cb_toggle_clock(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id != ADMIN_ID:
        await callback.answer("Faqat admin!", show_alert=True)
        return
    current = is_clock_enabled()
    set_clock_enabled(not current)
    new_st = "YOQILDI 🟢" if not current else "O'CHIRILDI 🔴"
    await callback.answer(f"Profil Soati {new_st}!", show_alert=True)
    try:
        await callback.message.edit_text(build_settings_panel(user_id), parse_mode=None, reply_markup=get_settings_keyboard(user_id))
    except Exception:
        pass


@router.callback_query(F.data == "clear_chat_history")
async def cb_clear_chat_history(callback: types.CallbackQuery):
    clear_history(callback.message.chat.id)
    await callback.answer("🗑 Suhbat tarixi tozalandi!", show_alert=True)


@router.callback_query(F.data == "refresh_panel")
async def cb_refresh_panel(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    await callback.answer("Yangilandi! 🔄")
    try:
        await callback.message.edit_text(build_settings_panel(user_id), parse_mode=None, reply_markup=get_settings_keyboard(user_id))
    except Exception:
        pass


# ─────────────────────────────────────────────────────────
# PRIVATE CHAT MESSAGES
# ─────────────────────────────────────────────────────────
@router.message(F.chat.type == "private")
async def handle_private_message(message: types.Message, bot: Bot):
    text = message.text.strip() if message.text else ""

    # .ok — media saqlash
    if text.lower() == ".ok" and message.reply_to_message:
        success = await media_service.save_temporary_media(bot, message, message.chat.id)
        if success:
            await message.reply("✅ Media shaxsiy chatingizga saqlandi!")
        else:
            await message.reply("❌ Mediani saqlashda xatolik.")
        return

    # Userbot buyruqlari shaxsiy chatda ham ishlaydi (hohlagan joyda)
    if text.startswith(".") and len(text) > 1:
        from handlers.business_message import handle_owner_command, _dedupe_command
        if _dedupe_command(message.chat.id, message.from_user.id, text):
            return
        parts = text.split(maxsplit=1)
        cmd_word = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        if cmd_word == ".ok":
            return  # .ok reply'siz — hech narsa qilmaydi
        handled = await handle_owner_command(bot, message, None, cmd_word, args)
        if not handled:
            await message.answer("❓ Noma'lum buyruq.\n\nBarcha buyruqlar: .help", parse_mode=None)
        return

    # Typing indicator
    try:
        await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    except Exception:
        pass

    # Media processing
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
        await message.answer("Kechirasiz, bu turdagi xabar qo'llab-quvvatlanmaydi.", parse_mode=None)
        return

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

    try:
        reply_text = await claude_service.generate_response(
            contents=final_contents,
            system_prompt=settings.default_system_prompt,
        )
    except Exception as e:
        logger.error(f"AI error in private chat: {e}", exc_info=True)
        reply_text = "Kechirasiz, vaqtinchalik xatolik yuz berdi."

    add_message(message.chat.id, "assistant", reply_text)

    try:
        await message.answer(text=reply_text, parse_mode=None)
    except Exception as e:
        logger.error(f"Failed to send private reply: {e}", exc_info=True)
