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
from app.keyboards.menu import get_main_reply_keyboard
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
  <code>.ai [savol]</code> — Gemini 2.5 Flash bilan muloqot
  <code>.gemini [savol]</code> — Gemini AI

🌐 <b>Asboblar va Tarjima:</b>
  <code>.tr [til] [matn]</code> — Google Translate
  <code>.tts [matn]</code> — Matnni ovozga aylantirish (Speech)
  <code>.weather [shahar]</code> — Ob-havo (Toshkent, Xorazm va b.)
  <code>.currency</code> / <code>.kurs</code> — Markaziy bank kursi
  <code>.shortlink [url]</code> — URL qisqartirish
  <code>.gender [ism]</code> — Jins taxmini
  <code>.telegraph Sarlavha | Matn</code> — Maqola yaratish

🎭 <b>Animatsiyalar:</b>
  <code>.love</code>, <code>.snow</code>, <code>.xd</code>, <code>.police</code>, <code>.kill</code> ...

📥 <b>Media va Saqlash:</b>
  <code>.yt [qidiruv]</code> — YouTube qidiruv
  <code>.ok</code> — Javobdagi mediani shaxsiy chatga saqlash
  <code>.catbox</code>, <code>.envs</code>, <code>.0x0</code>, <code>.tmpfiles</code> — Fayl yuklash

🎮 <b>O'yin va RolePlay:</b>
  <code>.me</code>, <code>.do</code>, <code>.try</code>, <code>.todo</code>, <code>.ro</code>
  <code>.co</code> — Barcha modullar ro'yxati
"""

async def build_settings_view(user_id: int):
    is_admin = user_id in settings.admin_ids
    async with async_session() as session:
        conn = await get_user_connection(session, user_id)
        conn_id = conn.connection_id if conn else f"user_{user_id}"
        curr_m = "gemini"
        is_en = conn.is_enabled if conn else True
        clock_on = conn.clock_on if conn else False

    text = (
        f"⚙️ <b>BOT BOSHQARUV PANELI</b>\n\n"
        f"👤 Foydalanuvchi ID: <code>{user_id}</code>\n"
        f"🤖 AI Model: <code>GEMINI 2.5 FLASH</code>\n"
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
        f"Quyidagi menyu tugmalari va dot-buyruqlar (.help, .co) orqali boshqarishingiz mumkin."
    )
    await message.answer(welcome, parse_mode="HTML", reply_markup=get_main_reply_keyboard(is_admin))

@router.message(Command("help"))
@router.message(F.text == "📖 Yordam")
async def cmd_help(message: types.Message):
    await message.answer(USERBOT_HELP_TEXT, parse_mode="HTML", reply_markup=get_breadcrumbs_keyboard("home"))

@router.message(Command("settings"))
@router.message(F.text.in_({"⚙️ Sozlamalar", "🎛 AI Sozlamalar"}))
async def cmd_settings(message: types.Message):
    text, kb = await build_settings_view(message.from_user.id)
    await message.answer(text, parse_mode="HTML", reply_markup=kb)

@router.message(Command("profile"))
@router.message(F.text == "👤 Profilim")
async def cmd_profile(message: types.Message):
    u = message.from_user
    text = (
        f"👤 <b>PROFIL MA'LUMOTLARI</b>\n\n"
        f"🆔 <b>ID:</b> <code>{u.id}</code>\n"
        f"👤 <b>Ism:</b> {u.full_name}\n"
        f"🏷 <b>Username:</b> @{u.username if u.username else 'yo\'q'}\n"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_breadcrumbs_keyboard("home"))

@router.message(F.text == "🤖 Gemini 2.5 Flash AI")
async def cmd_reply_ai_info(message: types.Message):
    text = (
        "🤖 <b>Gemini 2.5 Flash AI</b>\n\n"
        "⚡️ Yagona rasmiy va cheksiz tezkor AI modeli aktivlashtirilgan.\n"
        "Muloqot qilish uchun har qanday chatda <code>.ai [savol]</code> deb yozing yoki Telegram Business ulangan chatlarda to'g'ridan-to'g'ri javob beradi."
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_breadcrumbs_keyboard("home"))

@router.message(F.text == "🧩 Plaginlar va Buyruqlar")
async def cmd_reply_plugins(message: types.Message):
    await plugin_manager.dispatch(".co", types.Bot.get_current(), message, "", "")

@router.message(F.text == "💼 Business Ulanish")
async def cmd_reply_business(message: types.Message):
    text = (
        "💼 <b>Telegram Business UlanishYo'riqnomasi:</b>\n\n"
        "1. Telegram Sozlamalari ⚙️ ga kiring\n"
        "2. <b>Telegram Business</b> bo'limini tanlang\n"
        "3. <b>Chat Botlar (Chat Bots)</b> bo'limiga kiring\n"
        "4. Ushbu botni ro'yxatdan tanlab saqlang!\n\n"
        "✅ Shundan so'ng bot sizning hisobingizga kelgan xabarlarga avtomatik o'zbek tilida javob bera boshlaydi."
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_breadcrumbs_keyboard("home"))

@router.message(Command("admin"))
@router.message(F.text == "👑 Admin Panel")
async def cmd_reply_admin(message: types.Message):
    user_id = message.from_user.id
    if user_id not in settings.admin_ids:
        await message.answer("⚠️ Faqat admin uchun!", parse_mode=None)
        return
    await message.answer("👑 <b>ADMIN PANEL</b>", parse_mode="HTML", reply_markup=get_admin_keyboard())

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
            ".ai, .weather, .tr, .yt, .currency, .shortlink, .gender, .tts, .telegraph, .love, .me, .do, .try, .todo, .ro, .catbox, .acc, .time, .co",
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
            await update_conn_settings(session, cid, model="gemini")
        await callback.answer("✅ Model GEMINI 2.5 FLASH ga o'zgartirildi!", show_alert=True)
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

# ── ALL CHAT DOT-COMMAND HANDLER WITH FUZZY MATCHING ──
@router.message(F.text.startswith(".") | F.caption.startswith("."))
async def handle_chat_commands(message: types.Message, bot: types.Bot):
    text = (message.text or message.caption or "").strip()
    if not (text.startswith(".") and len(text) > 1):
        return

    parts = text.split(maxsplit=1)
    cmd_word = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    if cmd_word in (".help", ".co", ".func", ".komandalar"):
        await plugin_manager.dispatch(".co", bot, message, "", args)
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
        await message.answer(resp, parse_mode="HTML")
