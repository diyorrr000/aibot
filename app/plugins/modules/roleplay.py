import random
from aiogram import Bot, types

async def send_fb(bot: Bot, message: types.Message, conn_id: str, text: str, parse_mode="HTML"):
    try:
        await bot.send_message(chat_id=message.chat.id, text=text, business_connection_id=conn_id, parse_mode=parse_mode)
    except Exception:
        await bot.send_message(chat_id=message.chat.id, text=text, parse_mode=parse_mode)

async def cmd_me(bot: Bot, message: types.Message, conn_id: str, args: str):
    text = args.strip() or "biror narsa qildi"
    user_name = message.from_user.first_name if message.from_user else "Foydalanuvchi"
    await send_fb(bot, message, conn_id, f"🌀 <i>{user_name} {text}</i>")

async def cmd_do(bot: Bot, message: types.Message, conn_id: str, args: str):
    text = args.strip() or "voqea sodir bo'ldi"
    await send_fb(bot, message, conn_id, f"🌐 <i>Atrofda: {text}</i>")

async def cmd_try(bot: Bot, message: types.Message, conn_id: str, args: str):
    action = args.strip() or "harakat"
    res = random.choice(["✅ Muvaffaqiyatli!", "❌ Omadsiz!"])
    user_name = message.from_user.first_name if message.from_user else "Foydalanuvchi"
    await send_fb(bot, message, conn_id, f"🎲 <i>{user_name} {action} ga urindi...</i>\n\nNatija: <b>{res}</b>")

async def cmd_todo(bot: Bot, message: types.Message, conn_id: str, args: str):
    parts = args.split(maxsplit=1)
    phrase = parts[0] if parts else "Salom"
    action = parts[1] if len(parts) > 1 else "kulimsirab"
    user_name = message.from_user.first_name if message.from_user else "Foydalanuvchi"
    await send_fb(bot, message, conn_id, f'💬 "{phrase}" - <i>dedi {user_name}, {action}</i>')

async def cmd_roulette(bot: Bot, message: types.Message, conn_id: str, args: str):
    bullet = random.randint(1, 6)
    if bullet == 1:
        msg = "🎰 <b>BOOM! 💥 Siz yutqazdingiz!</b>"
    else:
        msg = "🎰 <b>Klick... Bosh o'q! Omon qoldingiz! 😅</b>"
    await send_fb(bot, message, conn_id, msg)

def register(pm):
    pm.register_command(".me", cmd_me)
    pm.register_command(".do", cmd_do)
    pm.register_command(".try", cmd_try)
    pm.register_command(".todo", cmd_todo)
    pm.register_command(".roulette", cmd_roulette)
    pm.register_command(".ro", cmd_roulette)
