import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from app.config.settings import settings
from app.keyboards.inline import (
    get_main_menu_keyboard,
    get_breadcrumbs_keyboard,
    get_settings_keyboard,
    get_admin_keyboard,
)
from app.database.connection import async_session
from app.database.repository import (
    get_user_connection,
    get_all_business_connections,
    clear_chat_history,
    update_conn_settings,
)
from app.plugins.manager import plugin_manager
from app.services.animation import ANIMATIONS, run_aiogram_animation

logger = logging.getLogger(__name__)
router = Router()

USERBOT_HELP_TEXT = """📋 <b>USERBOT BUYRUQLAR RO'YXATI</b>

🤖 <b>AI Modellar:</b>
  <code>.ai [savol]</code> — AI bilan muloqot
  <code>.grok [savol]</code> — Grok 4.3 AI
  <code>.gpt [savol]</code> — GPT 4o AI
  <code>.model claude|grok|gpt|gemini</code> — Modelni pinlash

🌐 <b>Asboblar va Tarjima:</b>
  <code>.tr [til] [matn]</code> — Google Translate
  <code>.tts [matn]</code> — Matnni ovozga aylantirish
  <code>.weather [shahar]</code> — Ob-havo
  <code>.currency</code> / <code>.kurs</code> — Markaziy bank kursi
  <code>.shortlink [url]</code> — URL qisqartirish
  <code>.gender [ism]</code> — Jins taxmini
  <code>.telegraph Sarlavha | Matn</code> — Maqola yaratish

🎭 <b>Animatsiyalar:</b>
  <code>.love</code>, <code>.snow</code>, <code>.xd</code>, <code>.police</code>, <code>.kill</code> ...

📥 <b>Media va Saqlash:</b>
  <code>.yt [qidiruv]</code> — YouTube qidiruv
  <code>.ok</code> — Javobdagi mediani shaxsiy chatga saqlash

🎮 <b>O'yin va RolePlay:</b>
  <code>.me</code>, <code>.do</code>, <code>.try</code>, <code>.todo</code>, <code>.ro</code>
"""

async def build_settings_view(user_id: int):
    is_admin = user_id in settings.admin_ids
    async with async_session() as session:
        conn = await get_user_connection(session, user_id)
        conn_id = conn.connection_id if conn else f"user_{user_id}"
        curr_m = conn.model if conn else settings.default_model
        is_en = conn.is_enabled if conn else True
        clock_on = conn.clock_on if conn else False

    text = (
        f"⚙️ <b>BOT BOSHQARUV PANELI</b>\n\n"
        f"👤 Foydalanuvchi ID: <code>{user_id}</code>\n"
        f"🤖 AI Model: <code>{curr_m.upper()}</code>\n"
        f"⚡ Avto-Javob: <code>{'YOQILGAN' if is_en else 'O\'CHIRILGAN'}</code>\n"
        f"🕒 Profil Soati: <code>{'YOQILGAN' if clock_on else 'O\'CHIRILGAN'}</code>\n"
    )
    kb = get_settings_keyboard(
        user_id=user_id,
        is_admin=is_admin,
        conn_id=conn_id,
        current_model=curr_m,
        is_enabled=is_en,
        clock_enabled=clock_on
    )
    return text, kb

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    is_admin = user_id in settings.admin_ids
    welcome = (
        f"👋 <b>Xush kelibsiz, {message.from_user.full_name}!</b>\n\n"
        f"🤖 <b>Telegram Business AI & Userbot Platformasi</b>\n"
        f"Tugmalar va dot-buyruqlar (.help) orqali barcha bo'limlarni boshqarishingiz mumkin."
    )
    await message.answer(welcome, parse_mode="HTML", reply_markup=get_main_menu_keyboard(is_admin))

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(USERBOT_HELP_TEXT, parse_mode="HTML", reply_markup=get_breadcrumbs_keyboard("home"))

@router.message(Command("settings"))
async def cmd_settings(message: types.Message):
    text, kb = await build_settings_view(message.from_user.id)
    await message.answer(text, parse_mode="HTML", reply_markup=kb)

@router.message(Command("profile"))
async def cmd_profile(message: types.Message):
    u = message.from_user
    text = (
        f"👤 <b>PROFIL MA'LUMOTLARI</b>\n\n"
        f"🆔 <b>ID:</b> <code>{u.id}</code>\n"
        f"👤 <b>Ism:</b> {u.full_name}\n"
        f"🏷 <b>Username:</b> @{u.username if u.username else 'yo\'q'}\n"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_breadcrumbs_keyboard("home"))

@router.callback_query(F.data.startswith("nav:"))
async def cb_navigation(callback: types.CallbackQuery):
    target = callback.data.split(":")[1]
    user_id = callback.from_user.id
    is_admin = user_id in settings.admin_ids

    if target == "home":
        await callback.message.edit_text(
            f"👋 <b>Boshqaruv Paneli</b>",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard(is_admin)
        )
    elif target in ("ai", "models"):
        text, kb = await build_settings_view(user_id)
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    elif target == "plugins":
        await callback.message.edit_text(
            "🧩 <b>Mavjud Plaginlar:</b>\n\n"
            ".weather, .tr, .yt, .currency, .shortlink, .gender, .tts, .telegraph, .love, .me, .do, .try, .todo, .ro",
            parse_mode="HTML",
            reply_markup=get_breadcrumbs_keyboard("home")
        )
    elif target == "profile":
        u = callback.from_user
        text = f"👤 <b>PROFIL</b>\n\nID: <code>{u.id}</code>\nIsm: {u.full_name}"
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_breadcrumbs_keyboard("home"))
    elif target == "settings":
        text, kb = await build_settings_view(user_id)
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    elif target == "help":
        await callback.message.edit_text(USERBOT_HELP_TEXT, parse_mode="HTML", reply_markup=get_breadcrumbs_keyboard("home"))
    elif target == "admin":
        if not is_admin:
            await callback.answer("⚠️ Faqat admin uchun!", show_alert=True)
            return
        await callback.message.edit_text("👑 <b>ADMIN PANEL</b>", parse_mode="HTML", reply_markup=get_admin_keyboard())

    await callback.answer()

@router.callback_query(F.data.startswith("set_model:"))
async def cb_set_model(callback: types.CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) == 3:
        conn_id, target_model = parts[1], parts[2]
        async with async_session() as session:
            conn = await get_user_connection(session, callback.from_user.id)
            cid = conn.connection_id if conn else conn_id
            await update_conn_settings(session, cid, model=target_model)
        await callback.answer(f"✅ Model {target_model.upper()} ga o'zgartirildi!", show_alert=True)
        text, kb = await build_settings_view(callback.from_user.id)
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)

@router.callback_query(F.data.startswith("action:"))
async def cb_actions(callback: types.CallbackQuery):
    action = callback.data.split(":")[1]
    user_id = callback.from_user.id

    if action == "clear_history":
        async with async_session() as session:
            await clear_chat_history(session, callback.message.chat.id)
        await callback.answer("🗑 Suhbat tarixi tozalandi!", show_alert=True)
    elif action == "toggle_auto":
        async with async_session() as session:
            conn = await get_user_connection(session, user_id)
            if conn:
                new_st = not conn.is_enabled
                await update_conn_settings(session, conn.connection_id, is_enabled=new_st)
                await callback.answer(f"Avto-Javob {'YOQILDI 🟢' if new_st else 'O\'CHIRILDI 🔴'}!", show_alert=True)
            else:
                await callback.answer("⚠️ Business hisob ulash lozim!", show_alert=True)
        text, kb = await build_settings_view(user_id)
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    elif action == "toggle_global_clock":
        async with async_session() as session:
            conn = await get_user_connection(session, user_id)
            if conn:
                new_st = not conn.clock_on
                await update_conn_settings(session, conn.connection_id, clock_on=new_st)
                await callback.answer(f"Profil Soati {'YOQILDI 🟢' if new_st else 'O\'CHIRILDI 🔴'}!", show_alert=True)
            else:
                await callback.answer("⚠️ Business hisob ulash lozim!", show_alert=True)
        text, kb = await build_settings_view(user_id)
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)

# ── PRIVATE & GROUP CHAT DOT-COMMAND HANDLER ──
@router.message(F.chat.type.in_({"private", "group", "supergroup"}))
async def handle_chat_commands(message: types.Message, bot: types.Bot):
    text = (message.text or message.caption or "").strip()
    if not (text.startswith(".") and len(text) > 1):
        return

    parts = text.split(maxsplit=1)
    cmd_word = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    if cmd_word == ".help":
        await message.answer(USERBOT_HELP_TEXT, parse_mode="HTML")
        return

    if cmd_word == ".ping":
        import time
        t0 = time.time()
        m = await message.answer("✅ <b>Ping: Tekshirilmoqda...</b>", parse_mode="HTML")
        t1 = time.time()
        ms = round((t1 - t0) * 1000)
        await m.edit_text(f"✅ <b>Ping: {ms} ms</b>", parse_mode="HTML")
        return

    anim_name = cmd_word.replace(".", "")
    if anim_name in ANIMATIONS:
        await run_aiogram_animation(bot, message.chat.id, anim_name)
        return

    handled = await plugin_manager.dispatch(cmd_word, bot, message, "", args)
    if not handled and message.chat.type == "private":
        await message.answer(f"❓ Noma'lum buyruq: <code>{cmd_word}</code>\nBarcha buyruqlar: /help", parse_mode="HTML")
