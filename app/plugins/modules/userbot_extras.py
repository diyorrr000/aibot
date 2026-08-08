import asyncio
import datetime
import io
import json
import os
import aiohttp
from aiogram import Bot, types
from aiogram.enums import ChatAction
from app.utils.helpers import get_uzb_now

AUTO_AD_TASKS = {}
FILE_READ_CACHE = {}
TIMER_CONFIG = {
    "date": "01.01.2027",
    "msg": "🎄 <b>Yangi yilgacha {date} qoldi!</b>\n🥰 <i>Yangi yilni do'stlar davrasida kutamiz</i>"
}

async def send_fb(bot: Bot, message: types.Message, conn_id: str, text: str, parse_mode="HTML"):
    try:
        await bot.send_message(chat_id=message.chat.id, text=text, business_connection_id=conn_id, parse_mode=parse_mode)
    except Exception:
        await bot.send_message(chat_id=message.chat.id, text=text, parse_mode=parse_mode)

# Account Info (.acc)
async def cmd_acc(bot: Bot, message: types.Message, conn_id: str, args: str):
    user = message.from_user
    if message.reply_to_message and message.reply_to_message.from_user:
        user = message.reply_to_message.from_user

    text = (
        f"👤 <b>Akkunt ma'lumoti:</b>\n\n"
        f"💎 <b>ID:</b> <code>{user.id}</code>\n"
        f"👤 <b>Ism:</b> {user.full_name}\n"
        f"🏷 <b>Username:</b> @{user.username if user.username else 'yo\'q'}\n"
        f"🤖 <b>Bot:</b> {'Ha' if user.is_bot else 'Yo\'q'}"
    )
    await send_fb(bot, message, conn_id, text)

# Anime Arts (.art, .nsfwart)
async def cmd_anime_arts(bot: Bot, message: types.Message, conn_id: str, args: str, nsfw: bool = False):
    category = "nsfw" if nsfw else "sfw"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.waifu.pics/{category}/waifu", timeout=aiohttp.ClientTimeout(total=15)) as resp:
                data = await resp.json()
                img_url = data.get("url")
                if img_url:
                    async with session.get(img_url) as r2:
                        img_bytes = await r2.read()
                        photo = types.BufferedInputFile(img_bytes, filename="anime.jpg")
                        caption = "🍿 <b>NSFW anime surat!</b>" if nsfw else "🍿 <b>Yoqimli anime surat!</b>"
                        await bot.send_photo(chat_id=message.chat.id, photo=photo, caption=caption, business_connection_id=conn_id)
                        return
        await send_fb(bot, message, conn_id, "🚫 <b>Surat yuklab bo'lmadi.</b>")
    except Exception as e:
        await send_fb(bot, message, conn_id, f"🚫 <b>Xato:</b> <code>{e}</code>")

# Auto Ad (.auto, .stopauto)
async def cmd_auto_ad(bot: Bot, message: types.Message, conn_id: str, args: str):
    if not args or "|" not in args:
        await send_fb(bot, message, conn_id, "🚫 <b>Format:</b> <code>.auto @guruhlink 60 | Sotiladi iPhone 15!</code>")
        return
    part1, ad_msg = [x.strip() for x in args.split("|", 1)]
    parts = part1.split()
    if len(parts) < 2:
        await send_fb(bot, message, conn_id, "🚫 <b>Format:</b> <code>.auto @guruhlink 60 | Xabar</code>")
        return
    target_chat, interval = parts[0], int(parts[1])

    if target_chat in AUTO_AD_TASKS:
        AUTO_AD_TASKS[target_chat].cancel()

    async def ad_loop():
        while True:
            try:
                await bot.send_message(chat_id=target_chat, text=ad_msg)
            except Exception:
                pass
            await asyncio.sleep(interval)

    AUTO_AD_TASKS[target_chat] = asyncio.create_task(ad_loop())
    await send_fb(bot, message, conn_id, f"✅ <b>Auto-reklama yoqildi!</b>\n👥 <code>{target_chat}</code> | ⏳ <code>{interval}s</code>")

async def cmd_stop_auto_ad(bot: Bot, message: types.Message, conn_id: str, args: str):
    target = args.strip()
    if target in AUTO_AD_TASKS:
        AUTO_AD_TASKS[target].cancel()
        del AUTO_AD_TASKS[target]
        await send_fb(bot, message, conn_id, f"✅ <b>{target} uchun reklama to'xtatildi!</b>")
    else:
        await send_fb(bot, message, conn_id, "🚫 <b>Faol reklama topilmadi.</b>")

# Timer (.time, .settime)
async def cmd_timer(bot: Bot, message: types.Message, conn_id: str, args: str):
    d_str = TIMER_CONFIG["date"]
    msg_template = TIMER_CONFIG["msg"]
    try:
        d_parts = d_str.split(".")
        target_date = datetime.datetime(int(d_parts[2]), int(d_parts[1]), int(d_parts[0]))
        now = datetime.datetime.now()
        diff = target_date - now
        if diff.total_seconds() < 0:
            await send_fb(bot, message, conn_id, "<b>Sana o'tib ketgan!</b> Sozlash: <code>.settime 31.12.2027 | Yangi yilgacha {date} qoldi</code>")
            return
        days = diff.days
        hours = diff.seconds // 3600
        minutes = (diff.seconds // 60) % 60
        seconds = diff.seconds % 60
        time_text = f"{days} kun, {hours} soat, {minutes} minut, {seconds} sekund"
        await send_fb(bot, message, conn_id, msg_template.format(date=time_text))
    except Exception as e:
        await send_fb(bot, message, conn_id, f"🚫 <b>Timer xatosi:</b> <code>{e}</code>")

async def cmd_set_timer(bot: Bot, message: types.Message, conn_id: str, args: str):
    if not args or "|" not in args:
        await send_fb(bot, message, conn_id, "🚫 <b>Format:</b> <code>.settime 01.01.2027 | Yangi yilgacha {date} qoldi</code>")
        return
    d_part, msg_part = [x.strip() for x in args.split("|", 1)]
    TIMER_CONFIG["date"] = d_part
    TIMER_CONFIG["msg"] = msg_part
    await send_fb(bot, message, conn_id, f"✅ <b>Timer sozlandi!</b> Sana: <code>{d_part}</code>")

# File Reader (.rf, .read)
async def cmd_read_file(bot: Bot, message: types.Message, conn_id: str, args: str):
    reply = message.reply_to_message
    if not reply or not reply.document:
        await send_fb(bot, message, conn_id, "🚫 <b>Faylga reply qiling (.txt)!</b>")
        return
    try:
        f_info = await bot.get_file(reply.document.file_id)
        file_bytes = await bot.download_file(f_info.file_path)
        content = file_bytes.read().decode("utf-8", errors="ignore")
        if len(content) > 3000:
            content = content[:3000] + "\n... (davomi bor)"
        await send_fb(bot, message, conn_id, f"📄 <b>Fayl: {reply.document.file_name}</b>\n\n<pre>{content}</pre>")
    except Exception as e:
        await send_fb(bot, message, conn_id, f"🚫 <b>O'qishda xato:</b> <code>{e}</code>")

# Quote Sticker (.q, .r)
async def cmd_quote_sticker(bot: Bot, message: types.Message, conn_id: str, args: str):
    reply = message.reply_to_message
    if not reply or not (reply.text or reply.caption):
        await send_fb(bot, message, conn_id, "💬 <b>Matnli xabarga reply qiling!</b>")
        return
    quote_text = args.strip() if args else (reply.text or reply.caption)
    u = reply.from_user if reply.from_user else message.from_user
    try:
        payload = {
            "type": "quote", "format": "webp", "backgroundColor": "#1b1429", "width": 512, "height": 512, "scale": 1.1,
            "messages": [{
                "entities": [], "avatar": True,
                "from": {"id": u.id, "first_name": u.first_name, "last_name": u.last_name or "", "username": u.username or ""},
                "text": quote_text, "replyMessage": {}
            }]
        }
        async with aiohttp.ClientSession() as session:
            async with session.post("https://bot.lyo.su/quote/generate", json=payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if "result" in data and "image" in data["result"]:
                        import base64
                        img_bytes = base64.b64decode(data["result"]["image"])
                        sticker = types.BufferedInputFile(img_bytes, filename="quote.webp")
                        await bot.send_sticker(chat_id=message.chat.id, sticker=sticker, business_connection_id=conn_id)
                        return
        await send_fb(bot, message, conn_id, "💬 <b>Stiker formatlab bo'lmadi.</b>")
    except Exception as e:
        await send_fb(bot, message, conn_id, f"🚫 <b>Quote xatosi:</b> <code>{e}</code>")

def register(pm):
    pm.register_command(".acc", cmd_acc)
    pm.register_command(".art", lambda b, m, c, a: cmd_anime_arts(b, m, c, a, nsfw=False))
    pm.register_command(".nsfwart", lambda b, m, c, a: cmd_anime_arts(b, m, c, a, nsfw=True))
    pm.register_command(".auto", cmd_auto_ad)
    pm.register_command(".stopauto", cmd_stop_auto_ad)
    pm.register_command(".time", cmd_timer)
    pm.register_command(".settime", cmd_set_timer)
    pm.register_command(".rf", cmd_read_file)
    pm.register_command(".read", cmd_read_file)
    pm.register_command(".q", cmd_quote_sticker)
    pm.register_command(".r", cmd_quote_sticker)
