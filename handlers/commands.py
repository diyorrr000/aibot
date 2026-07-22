import logging
from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from sqlalchemy.ext.asyncio import AsyncSession

from database.repository import (
    get_business_connection_by_user,
    get_or_create_settings,
    update_settings
)
from config import settings

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message, session: AsyncSession):
    user_id = message.from_user.id
    connection = await get_business_connection_by_user(session, user_id)

    status_str = "❌ Ulangan Telegram Business hisobi topilmadi"
    if connection:
        status_str = f"✅ Telegram Business ga ulangan! (Connection ID: `{connection.connection_id}`)"

    welcome_text = (
        f"👋 Assalomu alaykum, *{message.from_user.first_name or 'Foydalanuvchi'}*!\n\n"
        f"Men Telegram Business hisobingiz uchun **Gemini 2.5 Flash Lite AI Asistent** botman. 🚀\n\n"
        f"📊 **Joriy holat:** {status_str}\n\n"
        f"📖 **Ulanish yo'riqnomasi:**\n"
        f"1. Telegram Sozlamalar (**Settings**) -> **Telegram Business** -> **Chat Bots** bo'limiga kiring.\n"
        f"2. Ushbu botni tanlang va barcha ruxsatlarni berib saqlang.\n"
        f"3. Bot avtomatik ravishda mijozlaringizdan kelgan shaxsiy xabarlarga sizning nomingizdan javob berishni boshlaydi!\n\n"
        f"⚙️ **Buyruqlar:**\n"
        f"• /settings - Sozlamalarni ko'rish va boshqarish\n"
        f"• /setprompt <matn> - AI tizim yo'riqnomasini (Prompt) o'zgartirish\n"
        f"• /toggle - Avto-javobni yoqish / o'chirish\n"
        f"• /help - Yordam yo'riqnomasi"
    )
    await message.answer(welcome_text, parse_mode="Markdown")

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        f"📖 **Telegram Business Gemini Bot Yo'riqnomasi**\n\n"
        f"**Bot qanday ishlaydi?**\n"
        f"Ushbu bot Telegram Business funksiyasi orqali hisobingizga ulanadi. Mijoz sizga shaxsiy xabar yuborganda, bot Gemini 2.5 Flash Lite modelidan foydalanib sizning nomingizdan aqlli va tezkor javob qaytaradi.\n\n"
        f"✨ **Imkoniyatlari:**\n"
        f"- Matnli xabarlarga javob berish\n"
        f"- Rasmlarni tahlil qilish (Gemini Multimodal Vision)\n"
        f"- Ovozli xabarlarni eshitib javob berish (Gemini Multimodal Audio)\n"
        f"- Suhbat tarixini eslab qolish\n"
        f"- Maxsus yo'riqnoma (Prompt) bo'yicha ishlash\n\n"
        f"⚙️ **Sozlamalar:**\n"
        f"- Tizim yo'riqnomasini o'zgartirish: `/setprompt Yangi prompt matni`\n"
        f"- Avto-javobni to'xtatib turish: `/toggle`"
    )
    await message.answer(help_text, parse_mode="Markdown")

@router.message(Command("settings"))
async def cmd_settings(message: types.Message, session: AsyncSession):
    user_id = message.from_user.id
    connection = await get_business_connection_by_user(session, user_id)

    if not connection:
        await message.answer("⚠️ Botingiz hali Telegram Business hisobiga ulanmagan. Iltimos, Telegram Business sozlamalarida botni ulang.")
        return

    biz_settings = await get_or_create_settings(
        session=session,
        connection_id=connection.connection_id,
        user_id=user_id,
        default_prompt=settings.default_system_prompt,
        default_model="gemini-2.5-flash-lite"
    )

    auto_status = "✅ Yoqilgan" if biz_settings.is_auto_reply_enabled else "❌ O'chirilgan"

    text = (
        f"⚙️ **Telegram Business Bot Sozlamalari**\n\n"
        f"🆔 **Connection ID:** `{connection.connection_id}`\n"
        f"🤖 **Model:** `gemini-2.5-flash-lite`\n"
        f"⚡ **Avto-javob holati:** {auto_status}\n\n"
        f"📝 **Tizim Yo'riqnomasi (System Prompt):**\n"
        f"_{biz_settings.system_prompt}_\n\n"
        f"👉 Yo'riqnomani o'zgartirish uchun `/setprompt <matn>` yozing.\n"
        f"👉 Avto-javobni yoqish/o'chirish uchun `/toggle` yozing."
    )
    await message.answer(text, parse_mode="Markdown")

@router.message(Command("setprompt"))
async def cmd_set_prompt(message: types.Message, command: CommandObject, session: AsyncSession):
    user_id = message.from_user.id
    connection = await get_business_connection_by_user(session, user_id)

    if not connection:
        await message.answer("⚠️ Hali Telegram Business hisobi ulanmagan.")
        return

    new_prompt = command.args
    if not new_prompt:
        await message.answer("⚠️ Iltimos, yangi prompt matnini kiriting.\nMasalan: `/setprompt Siz kiyim-kechak do'koni yordamchisisiz. Narxlarni aytib bering.`", parse_mode="Markdown")
        return

    await update_settings(session, connection.connection_id, system_prompt=new_prompt)
    await message.answer("✅ Tizim yo'riqnomasini (System Prompt) muvaffaqiyatli yangilandi!")

@router.message(Command("toggle"))
async def cmd_toggle(message: types.Message, session: AsyncSession):
    user_id = message.from_user.id
    connection = await get_business_connection_by_user(session, user_id)

    if not connection:
        await message.answer("⚠️ Hali Telegram Business hisobi ulanmagan.")
        return

    biz_settings = await get_or_create_settings(
        session=session,
        connection_id=connection.connection_id,
        user_id=user_id,
        default_prompt=settings.default_system_prompt,
        default_model="gemini-2.5-flash-lite"
    )

    new_status = not biz_settings.is_auto_reply_enabled
    await update_settings(session, connection.connection_id, is_auto_reply_enabled=new_status)

    status_msg = "✅ Avto-javob berish yoqildi!" if new_status else "❌ Avto-javob berish vaqtincha to'xtatildi!"
    await message.answer(status_msg)
