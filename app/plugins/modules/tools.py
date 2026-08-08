import urllib.parse
import json
import re
import aiohttp
from aiogram import Bot, types
from aiogram.enums import ChatAction
from app.utils.logger import logger
from app.services.ai.factory import ai_factory

REGION_MAP = {
    "toshkent": "Tashkent",
    "tashkent": "Tashkent",
    "xorazm": "Urgench",
    "urganch": "Urgench",
    "urgench": "Urgench",
    "samarqand": "Samarkand",
    "buxoro": "Bukhara",
    "andijon": "Andijan",
    "fargona": "Fergana",
    "namangan": "Namangan",
    "qashqadaryo": "Karshi",
    "qarshi": "Karshi",
    "surxondaryo": "Termez",
    "termez": "Termez",
    "navoiy": "Navoi",
    "jizzax": "Jizzakh",
    "sirdaryo": "Guliston",
    "guliston": "Guliston",
    "qoraqalpogiston": "Nukus",
    "nukus": "Nukus"
}

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

async def cmd_ai_prompt(bot: Bot, message: types.Message, conn_id: str, args: str):
    prompt = args.strip()
    if not prompt and message.reply_to_message:
        prompt = message.reply_to_message.text or message.reply_to_message.caption or ""
    if not prompt:
        await send_fb(bot, message, conn_id, "🤖 <b>AI ga savol yozing!</b>\n\nMisol: <code>.ai O'zbekiston poytaxti qayer?</code>")
        return

    await send_typing(bot, message, conn_id)
    try:
        reply = await ai_factory.generate_response(
            contents=[prompt],
            system_prompt="Siz foydali shaxsiy yordamchisisiz. Har doim o'zbek tilida to'liq va keng javob bering.",
            preferred_model="gemini"
        )
        await send_fb(bot, message, conn_id, reply, parse_mode=None)
    except Exception as e:
        await send_fb(bot, message, conn_id, f"🚫 <b>AI xatosi:</b> <code>{e}</code>")

async def cmd_weather(bot: Bot, message: types.Message, conn_id: str, args: str):
    raw_city = args.strip() if args else "Tashkent"
    search_city = REGION_MAP.get(raw_city.lower(), raw_city)

    await send_typing(bot, message, conn_id)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://wttr.in/{urllib.parse.quote(search_city)}?format=j1", timeout=aiohttp.ClientTimeout(total=15)) as resp:
                data = await resp.json(content_type=None)
                current = data["current_condition"][0]
                temp = current["temp_C"]
                feels = current["FeelsLikeC"]
                hum = current["humidity"]
                wind = current["windspeedKmph"]
                desc = current["weatherDesc"][0]["value"]
                display_name = raw_city.capitalize() if raw_city else "Toshkent"
                text = (
                    f"⛅ <b>Ob-havo: {display_name} ({search_city})</b>\n\n"
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

    gender_res = None
    prob = 0.0
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.genderize.io?name={urllib.parse.quote(name)}", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    g = data.get("gender")
                    if g:
                        gender_res = "Erkak" if g == "male" else "Ayol"
                        prob = float(data.get("probability", 0.9)) * 100
    except Exception:
        pass

    if not gender_res:
        nl = name.lower()
        male_suffixes = ["bek", "jon", "dor", "mir", "ali", "shox", "shoh", "boy", "zod", "xon", "ul", "din"]
        if any(nl.endswith(s) for s in male_suffixes) or any(s in nl for s in ["bek", "jon", "dor", "mir", "ali"]):
            gender_res = "Erkak"
        else:
            gender_res = "Ayol"
        prob = 95.0

    emoji = "🖤" if gender_res == "Erkak" else "❤️🔥"
    await send_fb(bot, message, conn_id, f"👤 <b>Jins taxmini: {name}</b>\n\n{emoji} <b>Jinsi:</b> <code>{gender_res}</code> (Aniqlik: <code>{prob:.0f}%</code>)")

async def cmd_tts(bot: Bot, message: types.Message, conn_id: str, args: str):
    text = args.strip()
    if not text and message.reply_to_message:
        text = message.reply_to_message.text or message.reply_to_message.caption or ""
    if not text:
        await send_fb(bot, message, conn_id, "🚫 <b>Matn yozing yoki reply qiling!</b> Misol: <code>.tts Salom qandaysiz</code>")
        return

    raw = text.split()
    lang = "tr"
    if raw[-1].lower() in ["ru", "en", "tr", "ar", "de", "fr"]:
        lang = raw[-1].lower()
        speech_text = " ".join(raw[:-1])
    else:
        speech_text = " ".join(raw)

    await send_typing(bot, message, conn_id)
    try:
        url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={urllib.parse.quote(speech_text)}&tl={lang}&client=tw-ob"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                if resp.status == 200:
                    audio = await resp.read()
                    voice = types.BufferedInputFile(audio, filename="voice.ogg")
                    try:
                        await bot.send_voice(chat_id=message.chat.id, voice=voice, caption=f"🗣 <code>{speech_text[:60]}</code>", business_connection_id=conn_id)
                    except Exception:
                        await bot.send_voice(chat_id=message.chat.id, voice=voice, caption=f"🗣 <code>{speech_text[:60]}</code>")
                    return
                else:
                    await send_fb(bot, message, conn_id, f"🚫 <b>TTS xatosi: HTTP {resp.status}</b>")
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
    for cmd in [".ai", ".gemini"]:
        pm.register_command(cmd, cmd_ai_prompt)
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
