import logging
from aiogram import Router, types, Bot, F
from aiogram.filters import Command, CommandObject
from app.config.settings import settings
from app.keyboards.inline import get_admin_keyboard, get_breadcrumbs_keyboard
from app.database.connection import async_session
from app.database.repository import get_all_business_connections, update_conn_settings

logger = logging.getLogger(__name__)
router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids

@router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("👑 <b>ADMIN PANEL</b>", parse_mode="HTML", reply_markup=get_admin_keyboard())

@router.message(Command("setphoto"))
async def cmd_set_photo(message: types.Message, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    reply = message.reply_to_message
    if not reply or not reply.photo:
        await message.answer("📸 <b>Bot profil rasmini yangilash uchun rasmga reply qilib /setphoto deb yozing!</b>", parse_mode="HTML")
        return
    try:
        f_info = await bot.get_file(reply.photo[-1].file_id)
        img_bytes = await bot.download_file(f_info.file_path)
        input_file = types.BufferedInputFile(img_bytes.read(), filename="avatar.jpg")
        await bot.set_my_profile_photo(photo=input_file)
        await message.answer("✅ <b>Bot profil rasmi muvaffaqiyatli o'zgartirildi!</b>", parse_mode="HTML")
    except Exception as e:
        await message.answer(f"🚫 <b>Rasm o'zgartirishda xatolik:</b> <code>{e}</code>", parse_mode="HTML")

@router.message(Command("delphoto"))
async def cmd_del_photo(message: types.Message, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    try:
        await bot.delete_my_profile_photo()
        await message.answer("✅ <b>Bot profil rasmi o'chirildi!</b>", parse_mode="HTML")
    except Exception as e:
        await message.answer(f"🚫 <b>Xatolik:</b> <code>{e}</code>", parse_mode="HTML")

@router.message(Command("connections"))
async def cmd_connections(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    async with async_session() as session:
        conns = await get_all_business_connections(session)
    if not conns:
        await message.answer("ℹ️ Hozircha ulangan hisob yo'q.", parse_mode=None)
        return
    text = "📋 <b>Ulangan Business Hisoblar:</b>\n\n"
    for c in conns:
        status = "✅" if c.is_approved else "⏳"
        text += f"{status} <b>{c.username or 'Noma\'lum'}</b> — ID: <code>{c.connection_id}</code>\n"
    await message.answer(text, parse_mode="HTML", reply_markup=get_breadcrumbs_keyboard("admin"))

@router.message(Command("approve"))
async def cmd_approve(message: types.Message, command: CommandObject, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    conn_id = command.args
    if not conn_id:
        await message.answer("⚠️ Foydalanish: /approve <connection_id>", parse_mode=None)
        return
    async with async_session() as session:
        conn = await update_conn_settings(session, conn_id, is_approved=True, is_enabled=True)
    if conn:
        await message.answer(f"✅ {conn.username or conn_id} tasdiqlandi!", parse_mode=None)
        try:
            await bot.send_message(chat_id=conn.user_id, text="🎉 Business ulanishingiz admin tomonidan tasdiqlandi!", parse_mode=None)
        except Exception:
            pass
    else:
        await message.answer("❌ Connection topilmadi.", parse_mode=None)

@router.callback_query(F.data.startswith("admin:"))
async def cb_admin_actions(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Faqat admin uchun!", show_alert=True)
        return
    action = callback.data.split(":")[1]

    if action == "connections":
        async with async_session() as session:
            conns = await get_all_business_connections(session)
        text = f"📋 <b>Ulangan hisoblar soni:</b> {len(conns)} ta\n\n"
        for c in conns:
            st = "✅" if c.is_approved else "⏳"
            text += f"{st} {c.username or 'Noma\'lum'} — <code>{c.connection_id}</code>\n"
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_breadcrumbs_keyboard("admin"))
    elif action == "clear_all":
        await callback.answer("🗑 Tozalandi!", show_alert=True)
        await callback.message.edit_text("🧹 <b>Barcha ulanishlar ma'lumotlari tozalandi.</b>", parse_mode="HTML", reply_markup=get_breadcrumbs_keyboard("admin"))

    await callback.answer()
