import urllib.parse
import json
import re
import aiohttp
from aiogram import Bot, types
from aiogram.enums import ChatAction
from app.utils.logger import logger

async def send_fb(bot: Bot, message: types.Message, conn_id: str, text: str, parse_mode="HTML"):
    try:
        await bot.send_message(chat_id=message.chat.id, text=text, business_connection_id=conn_id, parse_mode=parse_mode)
    except Exception:
        await bot.send_message(chat_id=message.chat.id, text=text, parse_mode=parse_mode)

async def send_typing(bot: Bot, message: types.Message, conn_id: str):
    try:
        await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING, business_connection_id=conn_id)
    except Exception:
        pass

async def cmd_weather(bot: Bot, message: types.Message, conn_id: str, args: str):
    city = args.strip() if args else "Qarshi"
    await send_typing(bot, message, conn_id)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://wttr.in/{urllib.parse.quote(city)}?format=j1", timeout=aiohttp.ClientTimeout(total=15)) as resp:
                data = await resp.json(content_type=None)
                current = data["current_condition"][0]
                temp = current["temp_C"]
                feels = current["FeelsLikeC"]
                hum = current["humidity"]
                wind = current["windspeedKmph"]
                desc = current["weatherDesc"][0]["value"]
                text = (
                    f"⛅ <b>Ob-havo: {city}</b>\n\n"
                    f"🌏 <b>Holati:</b> <code>{desc}</code>\n"
                    f"🔥 <b>Harorat:</b> <code>{temp}°C</code> (Tuyulishi: <code>{feels}°C</code>)\n"
                    f"🌈 <b>Shamol:</b> <code>{wind} km/s</code> | 💧 <b>Namlik:</b> <code>{hum}%</code>"
                )
                await send_fb(bot, message, conn_id, text)
    except Exception as e:
        await send_fb(bot, message, conn_id, f"🚫 <b>Ob-havo xatosi:</b> <code>{e}</code>")

async def cmd_translate(bot: Bot, message: types.Message, conn_id: str, args: str):
    text = ""
    target_lang = "uz"
    if args:
        parts = args.split(maxsplit=1)
        target_lang = parts[0]
        if len(parts) > 1: text = parts[1]
    if not text and message.reply_to_message and message.reply_to_message.text:
        text = message.reply_to_message.text
    if not text:
        await send_fb(bot, message, conn_id, "🚫 <b>Tarjima uchun matn yozing yoki reply qiling!</b>\n\nMisol: <code>.tr en Salom dunyo</code>")
        return
    await send_typing(bot, message, conn_id)
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t&q={urllib.parse.quote(text)}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                data = await resp.json(content_type=None)
                translated = "".join(part[0] for part in data[0])
                await send_fb(bot, message, conn_id, f"🌐 <b>Tarjima (<code>{target_lang.upper()}</code>):</b>\n\n<blockquote>{translated}</blockquote>")
    except Exception as e:
        await send_fb(bot, message, conn_id, f"🚫 <b>Tarjima xatosi:</b> <code>{e}</code>")

async def cmd_currency(bot: Bot, message: types.Message, conn_id: str, args: str):
    await send_typing(bot, message, conn_id)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://cbu.uz/uz/arkhiv-kursov-valyut/json/", timeout=aiohttp.ClientTimeout(total=15)) as resp:
                data = await resp.json(content_type=None)
                main_vals = ["USD", "EUR", "RUB"]
                rows = []
                for item in data:
                    if item["Ccy"] in main_vals:
                        flag = "🇺🇸" if item["Ccy"] == "USD" else "🇪🇺" if item["Ccy"] == "EUR" else "🇷🇺"
                        rows.append(f"{flag} <b>1 {item['Ccy']}</b> = <code>{item['Rate']}</code> so'm ({item['Diff']})")
                text = f"💱 <b>Markaziy Bank Kurslari:</b>\n📅 <i>{data[0]['Date']}</i>\n\n" + "\n".join(rows)
                await send_fb(bot, message, conn_id, text)
    except Exception as e:
        await send_fb(bot, message, conn_id, f"🚫 <b>Valyuta xatosi:</b> <code>{e}</code>")

async def cmd_shortlink(bot: Bot, message: types.Message, conn_id: str, args: str):
    url = args.strip()
    if not url:
        await send_fb(bot, message, conn_id, "🚫 <b>URL yuboring!</b> Misol: <code>.shortlink https://google.com</code>")
        return
    await send_typing(bot, message, conn_id)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://is.gd/create.php", params={"format": "json", "url": url}, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                data = await resp.json(content_type=None)
                if "shorturl" in data:
                    await send_fb(bot, message, conn_id, f"✅ <b>Qisqa link:</b> <code>{data['shorturl']}</code>")
                else:
                    await send_fb(bot, message, conn_id, f"🚫 <b>Xato:</b> <code>{data.get('errormessage', 'Noma\'lum')}</code>")
    except Exception as e:
        await send_fb(bot, message, conn_id, f"🚫 <b>Shortlink xatosi:</b> <code>{e}</code>")

async def cmd_gender(bot: Bot, message: types.Message, conn_id: str, args: str):
    name = args.strip().lstrip("@")
    if not name and message.reply_to_message and message.reply_to_message.from_user:
        name = message.reply_to_message.from_user.first_name or ""
    if not name:
        await send_fb(bot, message, conn_id, "🚫 <b>Ism kiriting!</b> Misol: <code>.gender Sardor</code>")
        return
    await send_typing(bot, message, conn_id)
    gtext = "Erkak" if any(w in name.lower() for w in ["bek", "jon", "dor", "mir", "ali"]) else "Ayol"
    emoji = "🖤" if gtext == "Erkak" else "❤️🔥"
    await send_fb(bot, message, conn_id, f"👤 <b>Jins taxmini: {name}</b>\n\n{emoji} <b>Jinsi:</b> <code>{gtext}</code>")

async def cmd_tts(bot: Bot, message: types.Message, conn_id: str, args: str):
    if not args:
        await send_fb(bot, message, conn_id, "🚫 <b>Matn yozing!</b> Misol: <code>.tts Salom uz</code>")
        return
    raw = args.strip().split()
    lang = "uz"
    if raw[-1].lower() in ["uz", "ru", "en", "tr", "ar", "de", "fr"]:
        lang = raw[-1].lower()
        text = " ".join(raw[:-1])
    else:
        text = " ".join(raw)
    await send_typing(bot, message, conn_id)
    try:
        url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={urllib.parse.quote(text)}&tl={lang}&client=tw-ob"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                audio = await resp.read()
                voice = types.BufferedInputFile(audio, filename=f"voice_{lang}.ogg")
                await bot.send_voice(chat_id=message.chat.id, voice=voice, caption=f"🗣 <code>{text[:60]}</code>", business_connection_id=conn_id)
    except Exception as e:
        await send_fb(bot, message, conn_id, f"🚫 <b>TTS xatosi:</b> <code>{e}</code>")

async def cmd_telegraph(bot: Bot, message: types.Message, conn_id: str, args: str):
    if not args or "|" not in args:
        await send_fb(bot, message, conn_id, "🚫 <b>Format:</b> <code>.telegraph Sarlavha | Matn</code>")
        return
    title, content_text = [x.strip() for x in args.split("|", 1)]
    await send_typing(bot, message, conn_id)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.telegra.ph/createAccount?short_name=UserBot&author_name=UserBot") as r1:
                acc = await r1.json()
                token = acc["result"]["access_token"]
                content = [{"tag": "p", "children": [content_text]}]
                async with session.get(f"https://api.telegra.ph/createPage?access_token={token}&title={urllib.parse.quote(title)}&content={urllib.parse.quote(json.dumps(content))}") as r2:
                    page = await r2.json()
                    await send_fb(bot, message, conn_id, f"📝 <b>Maqola yaratildi!</b>\n🔗 {page['result']['url']}")
    except Exception as e:
        await send_fb(bot, message, conn_id, f"🚫 <b>Telegraph xatosi:</b> <code>{e}</code>")

def register(pm):
    pm.register_command(".weather", cmd_weather)
    pm.register_command(".tr", cmd_translate)
    pm.register_command(".currency", cmd_currency)
    pm.register_command(".kurs", cmd_currency)
    pm.register_command(".shortlink", cmd_shortlink)
    pm.register_command(".shlink", cmd_shortlink)
    pm.register_command(".gender", cmd_gender)
    pm.register_command(".tts", cmd_tts)
    pm.register_command(".t2s", cmd_tts)
    pm.register_command(".telegraph", cmd_telegraph)
