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
from app.database.repository import get_user_connection, get_all_business_connections, clear_chat_history, update_conn_settings

logger = logging.getLogger(__name__)
router = Router()

USERBOT_HELP_TEXT = """📋 <b>USERBOT BUYRUQLAR RO'YXATI</b>

🤖 <b>AI Modellar:</b>
  <code>.ai [savol]</code> — AI bilan muloqot
  <code>.grok [savol]</code> — Grok 4.3 AI
  <code>.gpt [savol]</code> — GPT 4o AI
  <code>.model claude|grok|gpt</code> — Modelni pinlash

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

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    is_admin = user_id in settings.admin_ids
    welcome = (
        f"👋 <b>Xush kelibsiz, {message.from_user.full_name}!</b>\n\n"
        f"🤖 <b>Telegram Business AI & Userbot Platformasi</b>\n"
        f"Tugmalar orqali barcha bo'limlarni boshqarishingiz mumkin."
    )
    await message.answer(welcome, parse_mode="HTML", reply_markup=get_main_menu_keyboard(is_admin))

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(USERBOT_HELP_TEXT, parse_mode="HTML", reply_markup=get_breadcrumbs_keyboard("home"))

@router.message(Command("settings"))
async def cmd_settings(message: types.Message):
    user_id = message.from_user.id
    is_admin = user_id in settings.admin_ids
    async with async_session() as session:
        conn = await get_user_connection(session, user_id)
        conn_id = conn.connection_id if conn else ""
        curr_m = conn.model if conn else settings.default_model
        is_en = conn.is_enabled if conn else True
    
    text = f"⚙️ <b>BOT BOSHQARUV PANELI</b>\n\nJoriy Model: <code>{curr_m.upper()}</code>"
    await message.answer(text, parse_mode="HTML", reply_markup=get_settings_keyboard(user_id, is_admin, conn_id, curr_m, is_en))

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
    elif target == "ai" or target == "models":
        await callback.message.edit_text(
            "🤖 <b>AI Modellari va Sozlamalari</b>\n\nQuyidagi tugmalar orqali modelni almashtiring:",
            parse_mode="HTML",
            reply_markup=get_breadcrumbs_keyboard("home")
        )
    elif target == "plugins":
        await callback.message.edit_text(
            "🧩 <b>Mavjud Plaginlar:</b>\n.weather, .tr, .yt, .currency, .shortlink, .gender, .tts, .telegraph, .love",
            parse_mode="HTML",
            reply_markup=get_breadcrumbs_keyboard("home")
        )
    elif target == "profile":
        u = callback.from_user
        text = f"👤 <b>PROFIL</b>\n\nID: <code>{u.id}</code>\nIsm: {u.full_name}"
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_breadcrumbs_keyboard("home"))
    elif target == "settings":
        async with async_session() as session:
            conn = await get_user_connection(session, user_id)
            conn_id = conn.connection_id if conn else ""
            curr_m = conn.model if conn else settings.default_model
            is_en = conn.is_enabled if conn else True
        await callback.message.edit_text(
            "⚙️ <b>Sozlamalar Paneli:</b>",
            parse_mode="HTML",
            reply_markup=get_settings_keyboard(user_id, is_admin, conn_id, curr_m, is_en)
        )
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
            await update_conn_settings(session, conn_id, model=target_model)
        await callback.answer(f"✅ Model {target_model.upper()} ga o'zgartirildi!", show_alert=True)
        user_id = callback.from_user.id
        is_admin = user_id in settings.admin_ids
        await callback.message.edit_text("⚙️ <b>Sozlamalar yangilandi!</b>", parse_mode="HTML", reply_markup=get_settings_keyboard(user_id, is_admin, conn_id, target_model))

@router.callback_query(F.data == "action:clear_history")
async def cb_clear_history(callback: types.CallbackQuery):
    async with async_session() as session:
        await clear_chat_history(session, callback.message.chat.id)
    await callback.answer("🗑 Suhbat tarixi tozalandi!", show_alert=True)
