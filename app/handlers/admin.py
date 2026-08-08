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

@router.callback_query(F.data == "admin:connections")
async def cb_admin_connections(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Faqat admin!", show_alert=True)
        return
    async with async_session() as session:
        conns = await get_all_business_connections(session)
    text = "📋 <b>Ulangan hisoblar soni:</b> " + str(len(conns)) + " ta"
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_breadcrumbs_keyboard("admin"))
    await callback.answer()
