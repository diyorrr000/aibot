"""
Aiogram-based implementation of all userbot plugin commands.

These commands work inside ANY chat through the Telegram Business API
(business_connection_id). No Telethon session is required — everything
is done via the bot (aiogram) + public HTTP APIs.

Every command handler signature:
    async def cmd_xxx(bot: Bot, message: types.Message, conn_id: str, args: str) -> None
"""
import asyncio
import bisect
import calendar
import io
import json
import logging
import os
import random
import re
import time
import urllib.parse
from datetime import datetime, timedelta, timezone

import aiohttp

from aiogram import Bot, types
from aiogram.enums import ChatAction

from storage import get_conn_settings, set_conn_setting, set_chat_model

logger = logging.getLogger(__name__)

CHECK = "✅"
ERROR = "🚫"

UZB_TZ = timezone(timedelta(hours=5))

# ─────────────────────────────────────────────────────────────
# HTTP HELPERS
# ─────────────────────────────────────────────────────────────

async def http_get_json(url: str, timeout: int = 20, **params):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
            resp.raise_for_status()
            return await resp.json(content_type=None)


async def http_get_bytes(url: str, timeout: int = 30, **params):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
            resp.raise_for_status()
            return await resp.read()


async def http_post_json(url: str, data=None, json_body=None, timeout: int = 30):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data, json=json_body, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
            text = await resp.text()
            try:
                return resp.status, json.loads(text)
            except Exception:
                return resp.status, text


async def send_text(bot: Bot, message: types.Message, conn_id: str, text: str, parse_mode="HTML"):
    """Send a message, preferring the business connection. Falls back to a
    normal bot message when the business connection can't reply in that chat."""
    try:
        await bot.send_message(
            chat_id=message.chat.id,
            text=text,
            business_connection_id=conn_id,
            parse_mode=parse_mode,
        )
        return
    except Exception as e:
        logger.debug(f"Business send failed (fallback to normal): {e}")
    await bot.send_message(
        chat_id=message.chat.id,
        text=text,
        parse_mode=parse_mode,
    )


async def send_typing(bot: Bot, message: types.Message, conn_id: str):
    try:
        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING,
            business_connection_id=conn_id,
        )
        return
    except Exception:
        pass
    try:
        await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────
# WEATHER  (.weather <shahar>)
# ─────────────────────────────────────────────────────────────

async def cmd_weather(bot, message, conn_id, args):
    city = args.strip() if args else "Qarshi"
    await send_typing(bot, message, conn_id)
    try:
        data = await http_get_json(f"https://wttr.in/{urllib.parse.quote(city)}?format=j1")
        current = data["current_condition"][0]
        temp = current["temp_C"]
        feels = current["FeelsLikeC"]
        hum = current["humidity"]
        wind = current["windspeedKmph"]
        desc = current["weatherDesc"][0]["value"]
        text = (
            f"⚡️ <b>Ob-havo: {city}</b>\n\n"
            f"🌏 <b>Holati:</b> <code>{desc}</code>\n"
            f"🔥 <b>Harorat:</b> <code>{temp}°C</code>\n"
            f"🌨 <b>Tuyulishi:</b> <code>{feels}°C</code>\n"
            f"🌈 <b>Shamol:</b> <code>{wind} km/soat</code>\n"
            f"💧 <b>Namlik:</b> <code>{hum}%</code>"
        )
        await send_text(bot, message, conn_id, text)
    except Exception as e:
        await send_text(bot, message, conn_id, f"{ERROR} <b>Ob-havoni olib bo'lmadi:</b> <code>{e}</code>")


# ─────────────────────────────────────────────────────────────
# TRANSLATOR  (.tr <til> <matn>)
# ─────────────────────────────────────────────────────────────

async def cmd_translate(bot, message, conn_id, args):
    text = ""
    target_lang = "uz"
    if args:
        parts = args.split(maxsplit=1)
        target_lang = parts[0]
        if len(parts) > 1:
            text = parts[1]
    if not text and message.reply_to_message and message.reply_to_message.text:
        text = message.reply_to_message.text
    if not text:
        await send_text(
            bot, message, conn_id,
            f"{ERROR} <b>Tarjima qilish uchun matn topilmadi!</b>\n\n"
            f"📝 <b>Namuna:</b> <code>.tr en Salom dunyo</code>"
        )
        return
    await send_typing(bot, message, conn_id)
    try:
        url = (
            "https://translate.googleapis.com/translate_a/single?"
            f"client=gtx&sl=auto&tl={target_lang}&dt=t&q={urllib.parse.quote(text)}"
        )
        result = await http_get_json(url)
        translated = "".join(part[0] for part in result[0])
        output = f"<b>Tarjima (<code>{target_lang.upper()}</code>):</b>\n\n<blockquote>{translated}</blockquote>"
        await send_text(bot, message, conn_id, output)
    except Exception as e:
        await send_text(bot, message, conn_id, f"{ERROR} <b>Tarjima xatosi:</b> <code>{e}</code>")


# ─────────────────────────────────────────────────────────────
# CURRENCY  (.kurs)
# ─────────────────────────────────────────────────────────────

async def cmd_currency(bot, message, conn_id, args):
    await send_typing(bot, message, conn_id)
    try:
        data = await http_get_json("https://cbu.uz/uz/arkhiv-kursov-valyut/json/")
        main_vals = ["USD", "EUR", "RUB"]
        rows = []
        for item in data:
            if item["Ccy"] in main_vals:
                flag = "🇺🇸" if item["Ccy"] == "USD" else "🇪🇺" if item["Ccy"] == "EUR" else "🇷🇺"
                rows.append(f"{flag} <b>1 {item['Ccy']}</b> = <code>{item['Rate']}</code> so'm ({item['Diff']})")
        text = (
            f"💰 <b>Markaziy Bank Kurslari:</b>\n"
            f"📅 <i>{data[0]['Date']}</i>\n\n" + "\n".join(rows)
        )
        await send_text(bot, message, conn_id, text)
    except Exception as e:
        await send_text(bot, message, conn_id, f"{ERROR} <b>Valyuta xatosi:</b> <code>{e}</code>")


# ─────────────────────────────────────────────────────────────
# LYRICS  (.lyrics <qo'shiq>)
# ─────────────────────────────────────────────────────────────

async def cmd_lyrics(bot, message, conn_id, args):
    song = args.strip() if args else ""
    if message.reply_to_message and message.reply_to_message.audio:
        a = message.reply_to_message.audio
        song = f"{a.performer or ''} - {a.title or ''}".strip(" -")
    if not song:
        await send_text(
            bot, message, conn_id,
            f"{ERROR} <b>Qo'shiq nomini kiriting!</b>\n\n📝 <b>Namuna:</b> <code>.lyrics Uzmir & Zilola - Ota</code>"
        )
        return
    await send_typing(bot, message, conn_id)
    try:
        status, data = await http_post_json(f"https://lyrist.vercel.app/api/{urllib.parse.quote(song)}")
        if status != 200 or "error" in data or not data.get("lyrics"):
            await send_text(bot, message, conn_id, f"{ERROR} <b>`{song}` uchun matn topilmadi.</b>")
            return
        title = data.get("title", song)
        artist = data.get("artist", "")
        lyrics = data.get("lyrics", "")
        if len(lyrics) > 3500:
            lyrics = lyrics[:3500] + "..."
        output = (
            f"📝 <b>Musiqa matni:</b>\n"
            f"🎵 <b>Nomi:</b> <code>{title}</code>\n"
            f"👤 <b>Ijrochi:</b> <code>{artist}</code>\n\n"
            f"<blockquote>{lyrics}</blockquote>"
        )
        await send_text(bot, message, conn_id, output)
    except Exception as e:
        await send_text(bot, message, conn_id, f"{ERROR} <b>Xatolik:</b> <code>{e}</code>")


# ─────────────────────────────────────────────────────────────
# SHORTLINK  (.shlink <url> / .shortlink <url>)
# ─────────────────────────────────────────────────────────────

URL_RE = re.compile(
    r'^(?:http|ftp)s?://'
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
    r'localhost|'
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    r'(?::\d+)?'
    r'(?:/?|[/?]\S+)$', re.IGNORECASE
)


async def cmd_shortlink(bot, message, conn_id, args):
    url = args.strip()
    if not url:
        await send_text(bot, message, conn_id, f"{ERROR} <b>Link kiriting!</b>\n\n📝 <b>Namuna:</b> <code>.shlink https://google.com</code>")
        return
    if not URL_RE.match(url):
        await send_text(bot, message, conn_id, f"{ERROR} <b>Haqiqiy URL yuboring!</b>\n\n📝 <b>Namuna:</b> <code>.shlink https://google.com</code>")
        return
    await send_typing(bot, message, conn_id)
    try:
        data = await http_get_json(f"https://is.gd/create.php", format="json", url=url)
        if "shorturl" in data:
            await send_text(
                bot, message, conn_id,
                f"{CHECK} <b>Link qisqartirildi!</b>\n\n"
                f"🔗 <b>Original:</b> <code>{url}</code>\n"
                f"🚀 <b>Qisqa link:</b> <code>{data['shorturl']}</code>"
            )
        else:
            await send_text(bot, message, conn_id, f"{ERROR} <b>Xato:</b> <code>{data.get('errormessage', 'Noma\'lum')}</code>")
    except Exception as e:
        await send_text(bot, message, conn_id, f"{ERROR} <b>Xato:</b> <code>{e}</code>")


# ─────────────────────────────────────────────────────────────
# GENDER GUESSER  (.gender <ism>)
# ─────────────────────────────────────────────────────────────

async def cmd_gender(bot, message, conn_id, args):
    name = args.strip() if args else ""
    if not name:
        if message.reply_to_message and message.reply_to_message.from_user:
            name = message.reply_to_message.from_user.first_name or ""
    if not name:
        await send_text(bot, message, conn_id, f"{ERROR} <b>Ism kiriting!</b>\n\n📝 <b>Namuna:</b> <code>.gender Sardor</code>")
        return
    name = name.lstrip("@")
    await send_typing(bot, message, conn_id)
    try:
        result = await http_get_json("https://api.genderize.io", name=name)
        g = result.get("gender")
        if g == "female":
            emoji, gtext = "❤️🔥", "Ayol"
        elif g == "male":
            emoji, gtext = "🖤", "Erkak"
        else:
            emoji, gtext = "🩵", "Noma'lum"
        await send_text(
            bot, message, conn_id,
            f"{CHECK} <b>Taxminiy jins: {name}</b>\n\n{emoji} <b>Jinsi:</b> <code>{gtext}</code>"
        )
    except Exception as e:
        await send_text(bot, message, conn_id, f"{ERROR} <b>Xatolik:</b> <code>{e}</code>")


# ─────────────────────────────────────────────────────────────
# TEXT 2 SPEECH  (.t2s <matn> [til])
# ─────────────────────────────────────────────────────────────

async def cmd_tts(bot, message, conn_id, args):
    if not args:
        await send_text(bot, message, conn_id, f"{ERROR} <b>Matn yozing!</b>\n\n📝 <b>Namuna:</b> <code>.t2s Salom uz</code> (uz, ru, en)")
        return
    raw = args.strip().split()
    lang = "uz"
    available = ["uz", "ru", "en", "tr", "ar", "de", "fr"]
    if raw[-1].lower() in available:
        lang = raw[-1].lower()
        text = " ".join(raw[:-1])
    else:
        text = " ".join(raw)
    if not text:
        await send_text(bot, message, conn_id, f"{ERROR} <b>Matn yozing!</b>")
        return
    await send_typing(bot, message, conn_id)
    try:
        url = (
            "https://translate.google.com/translate_tts"
            f"?ie=UTF-8&q={urllib.parse.quote(text)}&tl={lang}&client=tw-ob"
        )
        audio = await http_get_bytes(url, timeout=30)
        voice = types.BufferedInputFile(audio, filename=f"voice_{lang}.ogg")
        await bot.send_voice(
            chat_id=message.chat.id,
            voice=voice,
            caption=f"{CHECK} <b>Matn ovozga aylantirildi!</b>\n📝 <code>{text[:60]}</code>\n🌍 <i>{lang.upper()}</i>",
            business_connection_id=conn_id,
        )
    except Exception as e:
        await send_text(bot, message, conn_id, f"{ERROR} <b>TTS xatosi:</b> <code>{e}</code>")


# ─────────────────────────────────────────────────────────────
# TELEGRAPH  (.telegraph Sarlavha | Matn)
# ─────────────────────────────────────────────────────────────

async def cmd_telegraph(bot, message, conn_id, args):
    if not args or "|" not in args:
        await send_text(
            bot, message, conn_id,
            f"{ERROR} <b>Xato format!</b>\n\n📝 <b>Ishlatish:</b> <code>.telegraph Sarlavha | Maqola matni</code>"
        )
        return
    title, content_text = args.split("|", 1)
    title = title.strip()
    content_text = content_text.strip()
    await send_typing(bot, message, conn_id)
    try:
        acc = await http_get_json("https://api.telegra.ph/createAccount", short_name="UserBot", author_name="UserBot")
        if not acc.get("ok"):
            await send_text(bot, message, conn_id, f"{ERROR} <b>Akkunt yaratishda xato!</b>")
            return
        token = acc["result"]["access_token"]
        content = [{"tag": "p", "children": [content_text]}]
        page = await http_get_json(
            "https://api.telegra.ph/createPage",
            access_token=token, title=title, content=json.dumps(content), return_content="false",
        )
        if not page.get("ok"):
            await send_text(bot, message, conn_id, f"{ERROR} <b>Maqola yaratishda xato!</b>")
            return
        page_url = page["result"]["url"]
        await send_text(
            bot, message, conn_id,
            f"{CHECK} <b>Maqola yaratildi!</b>\n\n📝 <b>Sarlavha:</b> <code>{title}</code>\n🔗 <b>Havola:</b> {page_url}"
        )
    except Exception as e:
        await send_text(bot, message, conn_id, f"{ERROR} <b>Xatolik:</b> <code>{e}</code>")


# ─────────────────────────────────────────────────────────────
# YOUTUBE SEARCH  (.yt <savol>)
# ─────────────────────────────────────────────────────────────

async def cmd_yt_search(bot, message, conn_id, args):
    query = args.strip()
    if not query:
        await send_text(bot, message, conn_id, f"{ERROR} <b>Qidiruv matnini kiriting!</b>\n\n📝 <b>Namuna:</b> <code>.yt O'zbekiston</code>")
        return
    await send_typing(bot, message, conn_id)
    try:
        html = (await http_get_bytes("https://www.youtube.com/results", timeout=15, search_query=query)).decode("utf-8", errors="ignore")
        video_ids = re.findall(r"watch\?v=(\S{11})", html)
        if not video_ids:
            await send_text(bot, message, conn_id, f"{ERROR} <b>YouTube dan hech narsa topilmadi.</b>")
            return
        video_id = video_ids[0]
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        info = await http_get_json("https://noembed.com/embed", url=video_url)
        title = info.get("title", "Nomsiz video")
        author = info.get("author_name", "Noma'lum muallif")
        thumb = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
        caption = (
            f"{CHECK} <b>YouTube Qidiruv Natijasi:</b>\n\n"
            f"💻 <b>Nomi:</b> <code>{title}</code>\n"
            f"👤 <b>Kanal:</b> <code>{author}</code>\n\n"
            f"🔗 <b>Havola:</b> {video_url}"
        )
        try:
            img = await http_get_bytes(thumb)
            await bot.send_photo(
                chat_id=message.chat.id,
                photo=types.BufferedInputFile(img, filename="thumb.jpg"),
                caption=caption,
                business_connection_id=conn_id,
            )
        except Exception:
            await send_text(bot, message, conn_id, caption)
    except Exception as e:
        await send_text(bot, message, conn_id, f"{ERROR} <b>YouTube xatosi:</b> <code>{e}</code>")


# ─────────────────────────────────────────────────────────────
# RANDOM ANIME  (.ra / .anime)
# ─────────────────────────────────────────────────────────────

async def cmd_random_anime(bot, message, conn_id, args):
    await send_typing(bot, message, conn_id)
    try:
        data = await http_get_json("https://shikimori.one/api/animes", limit=1, order="random")
        anime = data[0]
        title = anime.get("russian") or anime.get("name")
        score = anime.get("score")
        episodes = anime.get("episodes")
        kind = anime.get("kind")
        img = f"https://shikimori.one{anime['image']['original']}"
        desc = ""
        try:
            full = await http_get_json(f"https://shikimori.one/api/animes/{anime['id']}")
            desc = (full.get("description") or "")[:500]
        except Exception:
            pass
        caption = (
            f"🍿 <b>Tasodifiy Anime:</b>\n\n"
            f"🎬 <b>Nomi:</b> <code>{title}</code>\n"
            f"⭐ <b>Reyting:</b> <code>{score}</code>\n"
            f"📦 <b>Turi:</b> <code>{kind}</code> | 📺 <b>Qismlar:</b> <code>{episodes}</code>"
        )
        if desc:
            caption += f"\n\n📖 <i>{desc}</i>"
        try:
            img_bytes = await http_get_bytes(img, timeout=20)
            await bot.send_photo(
                chat_id=message.chat.id,
                photo=types.BufferedInputFile(img_bytes, filename="anime.jpg"),
                caption=caption,
                business_connection_id=conn_id,
            )
        except Exception:
            await send_text(bot, message, conn_id, caption)
    except Exception as e:
        await send_text(bot, message, conn_id, f"{ERROR} <b>Anime xatosi:</b> <code>{e}</code>")


# ─────────────────────────────────────────────────────────────
# ANIME QUOTE  (.aq / .animequote)
# ─────────────────────────────────────────────────────────────

async def cmd_anime_quote(bot, message, conn_id, args):
    await send_typing(bot, message, conn_id)
    query = args.strip()
    quote = character = anime = None
    if query:
        urls = [
            f"https://animechan.xyz/api/random/anime?title={urllib.parse.quote(query)}",
            f"https://api.animechan.io/v1/quotes/random?anime={urllib.parse.quote(query)}",
        ]
    else:
        urls = [
            "https://animechan.xyz/api/random",
            "https://api.animechan.io/v1/quotes/random",
        ]
    last_err = None
    for url in urls:
        try:
            data = await http_get_json(url, timeout=15)
            if isinstance(data, dict) and data.get("data") and isinstance(data["data"], dict):
                d = data["data"]
                quote = d.get("content") or d.get("quote")
                character = (d.get("character") or {}).get("name") or d.get("character")
                anime = (d.get("anime") or {}).get("name") or d.get("anime")
            else:
                quote = data.get("quote")
                character = data.get("character")
                anime = data.get("anime")
            if quote:
                break
            last_err = Exception("bo'sh javob")
        except Exception as e:
            last_err = e
            continue
    if not quote:
        await send_text(
            bot, message, conn_id,
            f"{ERROR} <b>Sitat topishda xatolik:</b> <code>{last_err or 'Noma\'lum xato'}</code>"
        )
        return
    try:
        tr = await http_get_json(
            "https://translate.googleapis.com/translate_a/single",
            client="gtx", sl="auto", tl="uz", dt="t", q=quote,
        )
        quote = "".join(part[0] for part in tr[0]) or quote
    except Exception:
        pass
    output = (
        f"🍿 <b>Anime Sitatasi:</b>\n\n"
        f"<blockquote>{quote}</blockquote>\n"
        f"👤 <b>Qahramon:</b> <code>{character}</code>\n"
        f"🎬 <b>Anime:</b> <code>{anime}</code>"
    )
    await send_text(bot, message, conn_id, output)


# ─────────────────────────────────────────────────────────────
# ANIME ART  (.art)
# ─────────────────────────────────────────────────────────────

async def cmd_anime_art(bot, message, conn_id, args):
    await send_typing(bot, message, conn_id)
    img_url = None
    endpoints = [
        ("https://api.waifu.pics/sfw/waifu", "url"),
        ("https://nekos.best/api/v2/waifu", "results.0.url"),
        ("https://nekos.best/api/v2/neko", "results.0.url"),
    ]
    for url, path in endpoints:
        try:
            data = await http_get_json(url, timeout=15)
            cur = data
            for part in path.split("."):
                idx = int(part) if part.isdigit() else part
                cur = cur[idx]
            img_url = cur
            if img_url:
                break
        except Exception:
            continue
    if not img_url:
        await send_text(bot, message, conn_id, f"{ERROR} <b>Surat topilmadi.</b>")
        return
    try:
        img = await http_get_bytes(img_url, timeout=20)
        await bot.send_photo(
            chat_id=message.chat.id,
            photo=types.BufferedInputFile(img, filename="anime.jpg"),
            caption=f"🍿 <b>Yoqimli anime surat!</b>",
            business_connection_id=conn_id,
        )
    except Exception as e:
        await send_text(bot, message, conn_id, f"{ERROR} <b>Xatolik:</b> <code>{e}</code>")


# ─────────────────────────────────────────────────────────────
# COMMON HELPERS
# ─────────────────────────────────────────────────────────────

def owner_nickname(conn) -> str:
    fn = conn.get("first_name") or ""
    ln = conn.get("last_name") or ""
    return f"{fn} {ln}".strip() or "Foydalanuvchi"


# ─────────────────────────────────────────────────────────────
# AI DEEPSEEK  (.ai <savol> / reply)
# ─────────────────────────────────────────────────────────────

AI_SYSTEM_PROMPT = "Siz aqlli va foydali yordamchisiz. Har doim o'zbek tilida javob bering. Javoblaringiz qisqa va tushunarli bo'lsin."


async def ask_deepseek(query: str, system_prompt: str = AI_SYSTEM_PROMPT) -> str:
    """Ask DeepSeek (zecora0 endpoint) and return the answer text. Raises on failure."""
    status, data = await http_post_json(
        "https://zecora0.serv00.net/deepseek.php",
        data={"model": "2", "message": f"{system_prompt}\n\nSavol: {query}"},
        timeout=45,
    )
    if status != 200 or not (isinstance(data, dict) and data.get("success")):
        err = data.get("error", "Noma'lum xato") if isinstance(data, dict) else data
        raise Exception(f"DeepSeek xatosi: {err}")
    answer = str(data.get("response") or "").strip()
    if not answer:
        raise Exception("DeepSeek bo'sh javob qaytardi")
    return answer


async def cmd_model(bot, message, conn_id, args):
    """Pin the AI model for THIS chat: .model claude|grok|deepseek"""
    model = args.strip().lower().split()[0] if args.strip() else ""
    if model not in ("claude", "grok", "gpt", "deepseek"):
        await send_text(
            bot, message, conn_id,
            f"{ERROR} <b>Model tanlang!</b>\n\n"
            f"📝 <b>Namuna:</b> <code>.model claude</code>\n"
            f"🌐 <b>Modellar:</b> <code>claude</code> | <code>grok</code> | <code>gpt</code> | <code>deepseek</code>\n\n"
            f"ℹ️ Bu chat uchun model pinlanadi — boshqa model javob bermaydi."
        )
        return
    set_chat_model(conn_id, message.chat.id, model)
    names = {"claude": "🧠 Claude 4.5", "grok": "🌌 Grok 4.3", "gpt": "🤖 GPT 4o", "deepseek": "🤖 DeepSeek"}
    await send_text(
        bot, message, conn_id,
        f"{CHECK} <b>Model o'zgartirildi!</b>\n\n"
        f"Bu chatda endi <b>{names[model]}</b> javob beradi."
    )


async def cmd_ai(bot, message, conn_id, args):
    query = args.strip()
    if not query and message.reply_to_message and message.reply_to_message.text:
        query = message.reply_to_message.text.strip()
    if not query:
        await send_text(
            bot, message, conn_id,
            f"{ERROR} <b>AI ga savol bering!</b>\n\n"
            f"📝 <b>Namuna:</b> <code>.ai Salom</code> yoki reply qilib <code>.ai</code>"
        )
        return
    await send_typing(bot, message, conn_id)

    used_model = None
    answer = None

    # 1) DeepSeek
    try:
        answer = await asyncio.wait_for(
            ask_deepseek(query, AI_SYSTEM_PROMPT), timeout=50
        )
        used_model = "deepseek"
    except Exception:
        answer = None

    # 2) KILWA fallback zanjiri: qaysi model bo'sh bo'lsa o'sha javob beradi
    if not answer:
        from services.ai_service import claude_service
        chain = [
            ("claude", "Uzbekcha javob ber"),
            ("gpt", AI_SYSTEM_PROMPT),
            ("grok", AI_SYSTEM_PROMPT),
        ]
        for model, prompt in chain:
            try:
                gen = claude_service.generate_response(
                    contents=[query],
                    system_prompt=prompt,
                    model=model,
                    retries=1,
                    timeout=25,
                )
                answer = await asyncio.wait_for(gen, timeout=30)
                if answer:
                    used_model = model
                    break
            except Exception:
                continue

    if not answer:
        await send_text(
            bot, message, conn_id,
            f"{ERROR} <b>Barcha AI xizmatlari hozircha band.</b>\n"
            f"Qayta urinib ko'ring yoki <code>.gpt</code> / <code>.grok</code> bilan alohida sinang.",
            parse_mode=None,
        )
        return
    if len(answer) > 4000:
        answer = answer[:4000] + "..."
    await send_text(bot, message, conn_id, answer, parse_mode=None)
    if used_model:
        set_chat_model(conn_id, message.chat.id, used_model)


# ─────────────────────────────────────────────────────────────
# GROK AI  (.grok <savol> / reply)
# ─────────────────────────────────────────────────────────────

async def cmd_grok(bot, message, conn_id, args):
    query = args.strip()
    if not query and message.reply_to_message and message.reply_to_message.text:
        query = message.reply_to_message.text.strip()
    if not query:
        await send_text(
            bot, message, conn_id,
            f"{ERROR} <b>Grok ga savol bering!</b>\n\n"
            f"📝 <b>Namuna:</b> <code>.grok kelajak haqida ayt</code>"
        )
        return
    await send_typing(bot, message, conn_id)
    try:
        from services.grok_service import grok_service
        reply = await asyncio.wait_for(
            grok_service.generate_response(
                contents=[query],
                system_prompt="Siz foydali yordamchisiz. Har doim o'zbek tilida javob bering. Javoblaringiz qisqa va tushunarli bo'lsin.",
            ),
            timeout=45,
        )
        if len(reply) > 4000:
            reply = reply[:4000] + "..."
        await send_text(bot, message, conn_id, reply, parse_mode=None)
        set_chat_model(conn_id, message.chat.id, "grok")
    except asyncio.TimeoutError:
        await send_text(bot, message, conn_id, f"{ERROR} <b>Grok javob berishda kechikdi. Qayta urinib ko'ring.</b>")
    except Exception as e:
        await send_text(bot, message, conn_id, f"{ERROR} <b>Grok xatosi:</b> <code>{e}</code>", parse_mode=None)


# ─────────────────────────────────────────────────────────────
# GPT AI  (.gpt <savol> / reply) — KILWA kilwa-chatgpt
# ─────────────────────────────────────────────────────────────

async def cmd_gpt(bot, message, conn_id, args):
    query = args.strip()
    if not query and message.reply_to_message and message.reply_to_message.text:
        query = message.reply_to_message.text.strip()
    if not query:
        await send_text(
            bot, message, conn_id,
            f"{ERROR} <b>GPT ga savol bering!</b>\n\n"
            f"📝 <b>Namuna:</b> <code>.gpt Python nima?</code> yoki reply qilib <code>.gpt</code>"
        )
        return
    await send_typing(bot, message, conn_id)
    try:
        from services.claude_service import claude_service
        reply = await asyncio.wait_for(
            claude_service.generate_response(
                contents=[query],
                system_prompt="Siz foydali yordamchisiz. Har doim o'zbek tilida javob bering. Javoblaringiz qisqa va tushunarli bo'lsin.",
                model="gpt",
                retries=2,
            ),
            timeout=45,
        )
        if len(reply) > 4000:
            reply = reply[:4000] + "..."
        await send_text(bot, message, conn_id, reply, parse_mode=None)
        set_chat_model(conn_id, message.chat.id, "gpt")
    except asyncio.TimeoutError:
        await send_text(bot, message, conn_id, f"{ERROR} <b>GPT javob berishda kechikdi. Qayta urinib ko'ring.</b>")
    except Exception as e:
        await send_text(bot, message, conn_id, f"{ERROR} <b>GPT xatosi:</b> <code>{e}</code>", parse_mode=None)


async def _quote_generate(payload: dict, endpoints: list) -> bytes:
    """Generate a quote image, trying each endpoint in order.

    Handles both raw-binary responses (bot.lyo.su/quoteit) and base64-JSON
    responses (LyoSU quote-api). Raises with the last error if all fail.
    """
    last_err = None
    for url in endpoints:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=payload, timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status != 200:
                        last_err = Exception(f"status {resp.status}")
                        continue
                    body = await resp.read()
                    head = body[:100].decode("utf-8", errors="ignore").lstrip()
                    if head.startswith("{") or head.startswith("["):
                        try:
                            data = json.loads(body)
                            img = None
                            if isinstance(data, dict):
                                img = data.get("image") or (data.get("result") or {}).get("image")
                            if img:
                                import base64
                                return base64.b64decode(img)
                        except Exception:
                            pass
                        last_err = Exception("JSON javobda rasm topilmadi")
                        continue
                    if len(body) > 100:
                        return body
                    last_err = Exception("bo'sh javob")
        except Exception as e:
            last_err = e
            continue
    raise last_err or Exception("Noma'lum xato")


# ─────────────────────────────────────────────────────────────
# QUOTE STICKER  (.q — matnli xabarga reply)
# ─────────────────────────────────────────────────────────────

async def cmd_quote(bot, message, conn_id, args):
    reply = message.reply_to_message
    if not reply or not (reply.text or reply.caption):
        await send_text(
            bot, message, conn_id,
            f"{ERROR} <b>Matnli xabarga reply qiling!</b>\n\n📝 <b>Namuna:</b> <code>.q</code> (xabarga reply qilib)"
        )
        return
    await send_typing(bot, message, conn_id)
    text = reply.text or reply.caption
    sender = reply.from_user
    first = sender.first_name if sender else "User"
    last = sender.last_name if sender else ""
    username = sender.username if sender else ""
    user_id = sender.id if sender else 0
    payload = {
        "type": "quote",
        "format": "png",
        "backgroundColor": "#1b1b1b",
        "width": 512,
        "height": 768,
        "scale": 2,
        "messages": [
            {
                "entities": [],
                "avatar": True,
                "from": {
                    "id": user_id,
                    "first_name": first,
                    "last_name": last,
                    "username": username,
                    "language_code": "uz"
                },
                "text": text,
                "replyMessage": {}
            }
        ]
    }
    try:
        image_data = await _quote_generate(payload, [
            "https://bot.lyo.su/quoteit/generate",
            "https://shnwazdev-quoteapi.vercel.app/generate",
        ])
        img = types.BufferedInputFile(image_data, filename="quote.png")
        await bot.send_photo(
            chat_id=message.chat.id,
            photo=img,
            caption=f"{CHECK} <b>Quote tayyor!</b>",
            business_connection_id=conn_id,
        )
    except Exception as e:
        await send_text(bot, message, conn_id, f"{ERROR} <b>Quote API xatosi:</b> <code>{e}</code>")


# ─────────────────────────────────────────────────────────────
# SPOOF QUOTE  (.r <matn> — xabarga reply qiling)
# ─────────────────────────────────────────────────────────────

async def cmd_spoof_quote(bot, message, conn_id, args):
    text = args.strip()
    reply = message.reply_to_message
    if not text or not reply:
        await send_text(
            bot, message, conn_id,
            f"{ERROR} <b>Xato ishlatish!</b>\n\n📝 <b>Namuna:</b> <code>.r Salom dunyo</code> (xabarga reply qilib)"
        )
        return
    sender = reply.from_user
    first = sender.first_name if sender else "User"
    last = sender.last_name if sender else ""
    username = sender.username if sender else ""
    user_id = sender.id if sender else 0
    full_name = f"{first} {last}".strip() or "User"
    payload = {
        "type": "quote",
        "format": "webp",
        "backgroundColor": "#1b1429",
        "width": 512,
        "height": 512,
        "scale": 1.1,
        "messages": [
            {
                "entities": [],
                "avatar": True,
                "from": {
                    "id": user_id,
                    "first_name": first,
                    "last_name": last,
                    "username": username,
                    "language_code": "en",
                    "title": full_name
                },
                "text": text,
                "replyMessage": {},
                "date": int(time.time())
            }
        ]
    }
    try:
        image_bytes = await _quote_generate(payload, [
            "https://bot.lyo.su/quote/generate",
            "https://shnwazdev-quoteapi.vercel.app/generate",
        ])
        f = types.BufferedInputFile(image_bytes, filename="sticker.webp")
        await bot.send_document(
            chat_id=message.chat.id,
            document=f,
            caption=f"{CHECK} <b>Stiker tayyor!</b>",
            business_connection_id=conn_id,
        )
    except Exception as e:
        await send_text(bot, message, conn_id, f"{ERROR} <b>Stiker yasashda xato:</b> <code>{e}</code>")


# ─────────────────────────────────────────────────────────────
# RUSSIAN ROULETTE  (.ro / .roulette)
# ─────────────────────────────────────────────────────────────

ROULETTE_PUNISHMENTS = [
    "Ismni g'alati ismga o'zgartirish",
    "Botni qayta ishga tushirish",
    "Guruhdagilarni 'bezovta' qilish (tag)",
    "Hech narsa bo'lmadi, omadingiz bor ekan!"
]


async def cmd_roulette(bot, message, conn_id, args):
    bullet = random.randint(1, 5)
    current = random.randint(1, 5)
    try:
        msg = await bot.send_message(
            chat_id=message.chat.id,
            text=f"🔫 <b>To'pponchani o'qladingiz...</b>\n\n🔗 <b>O'q:</b> {current}/5\n\n👁️‍🗨️ <b>Hozir otamiz...</b>",
            business_connection_id=conn_id,
            parse_mode="HTML",
        )
        await asyncio.sleep(2)
        if bullet == current:
            punishment = random.choice(ROULETTE_PUNISHMENTS)
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=msg.message_id,
                text=f"🫨 <b>PAX! O'q tegdi.</b>\n\n😵‍💫 <b>Jazo:</b> <code>{punishment}</code>",
                business_connection_id=conn_id,
                parse_mode="HTML",
            )
        else:
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=msg.message_id,
                text=(
                    f"🙂 <b>Omadingiz keldi! O'q tegmasdan o'tib ketdi.</b>\n\n"
                    f"🔗 <b>Xavfli o'q:</b> {bullet}\n👁️‍🗨️ <b>Keyingi safar ehtiyot bo'ling!</b>"
                ),
                business_connection_id=conn_id,
                parse_mode="HTML",
            )
    except Exception as e:
        await send_text(bot, message, conn_id, f"{ERROR} <b>Xatolik:</b> <code>{e}</code>")


# ─────────────────────────────────────────────────────────────
# ROLEPLAY  (.me .do .try .todo)
# ─────────────────────────────────────────────────────────────

RP_EMOJI = "🌀"


async def cmd_me(bot, message, conn_id, args):
    if not args.strip():
        await send_text(bot, message, conn_id, f"{ERROR} <b>Harakatni yozing!</b>\n\n<blockquote>Namuna: <code>.me choy ichdi</code></blockquote>")
        return
    nick = owner_nickname(get_conn_settings(conn_id))
    await send_text(bot, message, conn_id, f"{RP_EMOJI} <b>{nick}</b> <i>{args.strip()}</i>")


async def cmd_do(bot, message, conn_id, args):
    if not args.strip():
        await send_text(bot, message, conn_id, f"{ERROR} <b>Voqeani yozing!</b>\n\n<blockquote>Namuna: <code>.do Quyosh chiqdi</code></blockquote>")
        return
    nick = owner_nickname(get_conn_settings(conn_id))
    await send_text(bot, message, conn_id, f"{RP_EMOJI} <i>{args.strip()}</i> - | <b>{nick}</b>")


async def cmd_try(bot, message, conn_id, args):
    if not args.strip():
        await send_text(bot, message, conn_id, f"{ERROR} <b>Harakatni yozing!</b>\n\n<blockquote>Namuna: <code>.try moshina o't oldi</code></blockquote>")
        return
    nick = owner_nickname(get_conn_settings(conn_id))
    result = random.choice(["<b>✅ Muvaffaqiyatli</b>", "<b>❌ Muvaffaqiyatsiz</b>"])
    await send_text(bot, message, conn_id, f"{RP_EMOJI} <b>{nick}</b> <i>{args.strip()}</i> - | {result}")


async def cmd_todo(bot, message, conn_id, args):
    raw = args.strip()
    if not raw or " " not in raw:
        await send_text(bot, message, conn_id, f"{ERROR} <b>Xato format!</b>\n\n<blockquote>Namuna: <code>.todo Salom. qo'l silkitib</code></blockquote>")
        return
    phrase, action = raw.split(maxsplit=1)
    nick = owner_nickname(get_conn_settings(conn_id))
    await send_text(bot, message, conn_id, f"{RP_EMOJI} <i>'{phrase}', - dedi </i><b>{nick}</b>, <i>{action}.</i>")


# ─────────────────────────────────────────────────────────────
# ACCOUNT INFO  (.acc / .acc <id> / reply)
# ─────────────────────────────────────────────────────────────

REG_DATA = {
    "1000000": 1380326400, "2768409": 1383264000, "7679610": 1388448000, "11538514": 1391212000,
    "15835244": 1392940000, "23646077": 1393459000, "38015510": 1393632000, "44634663": 1399334000,
    "46145305": 1400198000, "54845238": 1411257000, "63263518": 1414454000, "101260938": 1425600000,
    "101323197": 1426204000, "103151531": 1433376000, "103258382": 1432771000, "109393468": 1439078000,
    "111220210": 1429574000, "112594714": 1439683000, "116812045": 1437696000, "122600695": 1437782000,
    "124872445": 1439856000, "125828524": 1444003000, "130029930": 1441324000, "133909606": 1444176000,
    "143445125": 1448928000, "148670295": 1452211000, "152079341": 1453420000, "157242073": 1446768000,
    "171295414": 1457481000, "181783990": 1460246000, "222021233": 1465344000, "225034354": 1466208000,
    "278941742": 1473465000, "285253072": 1476835000, "294851037": 1479600000, "297621225": 1481846000,
    "328594461": 1482969000, "337808429": 1487707000, "341546272": 1487782000, "352940995": 1487894000,
    "369669043": 1490918000, "400169472": 1501459000, "616816630": 1529625600, "681896077": 1532821500,
    "727572658": 1543708800, "796147074": 1541371800, "925078064": 1563290000, "928636984": 1581513420,
    "1054883348": 1585674420, "1057704545": 1580393640, "1145856008": 1586342040, "1227964864": 1596127860,
    "1382531194": 1600188120, "1658586909": 1613148540, "1660971491": 1613329440, "1692464211": 1615402500,
    "1719536397": 1619293500, "1721844091": 1620224820, "1772991138": 1617540360, "1807942741": 1625520300,
    "1893429550": 1622040000, "1972424006": 1631669400, "1974255900": 1634000000, "2030606431": 1631992680,
    "2041327411": 1631989620, "2078711279": 1634321820, "2104178931": 1638353220, "2120496865": 1636714020,
    "2123596685": 1636503180, "2138472342": 1637590800, "3318845111": 1618028800, "4317845111": 1620028800,
    "5162494923": 1652449800, "5186883095": 1648764360, "5304951856": 1656718440, "5317829834": 1653152820,
    "5318092331": 1652024220, "5336336790": 1646368100, "5362593868": 1652024520, "5387234031": 1662137700,
    "5396587273": 1648014800, "5409444610": 1659025020, "5416026704": 1660925460, "5465223076": 1661710860,
    "5480654757": 1660926300, "5499934702": 1662130740, "5513192189": 1659626400, "5522237606": 1654167240,
    "5537251684": 1664269800, "5559167331": 1656718560, "5568348673": 1654642200, "5591759222": 1659025500,
    "5608562550": 1664012820, "5614111200": 1661780160, "5666819340": 1664112240, "5684254605": 1662134040,
    "5684689868": 1661304720, "5707112959": 1663803300, "5756095415": 1660925940, "5772670706": 1661539140,
    "5778063231": 1667477640, "5802242180": 1671821040, "5853442730": 1674866100, "5859878513": 1673117760,
    "5885964106": 1671081840, "5982648124": 1686941700, "6020888206": 1675534800, "6032606998": 1686998640,
    "6057123350": 1676198350, "6058560984": 1686907980, "6101607245": 1686830760, "6108011341": 1681032060,
    "6132325730": 1692033840, "6182056052": 1687870740, "6279839148": 1688399160, "6306077724": 1692442920,
    "6321562426": 1688486760, "6364973680": 1696349340, "6386727079": 1691696880, "6429580803": 1692082680,
    "6527226055": 1690289160, "6813121418": 1698489600, "6865576492": 1699052400, "6925870357": 1701192327,
    "7000000000": 1711889200, "7100000000": 1719772800, "7200000000": 1725148800, "7350000000": 1730454400,
    "7500000000": 1735776000, "7700000000": 1740960000, "7850000000": 1743638400, "8000000000": 1746316800,
    "8200000000": 1748995200, "8350000000": 1751673600, "8500000000": 1754352000,
}

def _estimate_registration(tg_id: int) -> float:
    items = sorted((int(k), v) for k, v in REG_DATA.items())
    keys = [k for k, _ in items]
    vals = [v for _, v in items]
    if tg_id <= keys[0]:
        t = vals[0]
    elif tg_id >= keys[-1]:
        t = vals[-1]
    else:
        i = bisect.bisect_left(keys, tg_id)
        x0, x1 = keys[i - 1], keys[i]
        y0, y1 = vals[i - 1], vals[i]
        t = y0 + (y1 - y0) * (tg_id - x0) / (x1 - x0)
    return min(t, time.time())

def _calc_age(date_str: str) -> str:
    d = datetime.strptime(date_str, "%d.%m.%Y")
    today = datetime.now()
    years = today.year - d.year
    months = today.month - d.month
    days = today.day - d.day
    if days < 0:
        months -= 1
        prev_month = 12 if d.month == 1 else d.month - 1
        prev_year = d.year - 1 if d.month == 1 else d.year
        days += calendar.monthrange(prev_year, prev_month)[1]
    if months < 0:
        years -= 1
        months += 12
    parts = []
    if years > 0:
        parts.append(f"{years} yil")
    if months > 0:
        parts.append(f"{months} oy")
    if days > 0:
        parts.append(f"{days} kun")
    return ", ".join(parts) if parts else "Yangi akkunt"


async def cmd_acc(bot, message, conn_id, args):
    reply = message.reply_to_message
    target_id = None
    name = "Akkunt"
    if reply and reply.from_user:
        target_id = reply.from_user.id
        name = reply.from_user.first_name or "Foydalanuvchi"
    elif args.strip().isdigit():
        target_id = int(args.strip())
    else:
        conn = get_conn_settings(conn_id)
        target_id = conn.get("user_id")
        name = owner_nickname(conn)
    if not target_id:
        await send_text(bot, message, conn_id, f"{ERROR} <b>Foydalanuvchi ID sini kiriting yoki xabarga reply qiling!</b>")
        return
    await send_typing(bot, message, conn_id)
    try:
        dc_id = ((target_id >> 22) % 5) + 1
        reg_time = _estimate_registration(target_id)
        reg_date = datetime.fromtimestamp(reg_time, tz=timezone.utc).strftime("%d.%m.%Y")
        age_str = _calc_age(reg_date)
        text = (
            f"✅ <b>{name} haqida ma'lumot</b>:\n\n"
            f"💎 <b>ID:</b> <code>{target_id}</code>\n"
            f"✈️ <b>Data-center:</b> <code>{dc_id}</code>\n"
            f"✅ <b>Ochilgan sana:</b> <code>{reg_date}</code>\n"
            f"🎲 <b>Akkunt yoshi:</b> <code>{age_str}</code>"
        )
        await send_text(bot, message, conn_id, text)
    except Exception as e:
        await send_text(bot, message, conn_id, f"{ERROR} <b>Xatolik:</b> <code>{e}</code>")


# ─────────────────────────────────────────────────────────────
# SERVER STATUS  (.status)
# ─────────────────────────────────────────────────────────────

async def cmd_status(bot, message, conn_id, args):
    text = "🖥 <b>Server holati:</b>\n\n"
    try:
        import psutil
        vm = psutil.virtual_memory()
        text += f"💾 <b>RAM:</b> <code>{vm.used / 1024**3:.2f} / {vm.total / 1024**3:.2f} GB</code>\n"
        text += f"📊 <b>CPU:</b> <code>{psutil.cpu_percent(interval=None)}%</code>\n"
        text += f"⚙️ <b>Bot xotirasi:</b> <code>{psutil.Process(os.getpid()).memory_info().rss / 1024**2:.2f} MB</code>\n"
    except ImportError:
        text += f"⚙️ <b>PID:</b> <code>{os.getpid()}</code>\n"
    text += f"🕒 <b>Vaqt:</b> <code>{datetime.now(UZB_TZ).strftime('%H:%M:%S')}</code>"
    await send_text(bot, message, conn_id, text)


# ─────────────────────────────────────────────────────────────
# PREMIUM EMOJI ID  (.getid)
# ─────────────────────────────────────────────────────────────

async def cmd_getid(bot, message, conn_id, args):
    target = message.reply_to_message or message
    for ent in (target.entities or []):
        if getattr(ent, "custom_emoji_id", None):
            await send_text(bot, message, conn_id, f"✅ <b>Premium Emoji ID:</b> <code>{ent.custom_emoji_id}</code>")
            return
    await send_text(bot, message, conn_id, f"{ERROR} <b>Bu xabarda premium emoji topilmadi!</b>")


# ─────────────────────────────────────────────────────────────
# TIMER  (.time / .settime)
# ─────────────────────────────────────────────────────────────

async def cmd_time(bot, message, conn_id, args):
    from storage import get_timer_config
    cfg = get_timer_config()
    try:
        d = datetime.strptime(cfg["date"], "%d.%m.%Y").replace(tzinfo=UZB_TZ)
        now = datetime.now(UZB_TZ)
        if d < now:
            await send_text(
                bot, message, conn_id,
                "<b>Sana o'tib ketgan yoki noto'g'ri!</b>\nSozlash uchun: <code>.settime 31.12.2026 | Yangi yilga</code>"
            )
            return
        diff = d - now
        days = diff.days
        hours = diff.seconds // 3600
        minutes = (diff.seconds // 60) % 60
        seconds = diff.seconds % 60
        time_text = (
            f"📅 <b>{days}</b> kun  |  "
            f"⏰ <b>{hours}</b> soat  |  "
            f"⏳ <b>{minutes}</b> minut  |  "
            f"⏱️ <b>{seconds}</b> sekund"
        )
        await send_text(bot, message, conn_id, cfg["msg"].format(date=time_text))
    except Exception:
        await send_text(
            bot, message, conn_id,
            "<b>Timer xatosi!</b>\nSozlash uchun <code>.settime</code> buyrug'idan foydalaning."
        )


async def cmd_settime(bot, message, conn_id, args):
    from storage import save_timer_config
    if not args.strip() or "|" not in args:
        await send_text(
            bot, message, conn_id,
            "<b>Xato format!</b>\n\n"
            "📝 <b>Namuna:</b> <code>.settime 01.01.2027 | Yangi yilgacha {date} qoldi</code>\n\n"
            "<i>{date} - qolgan vaqt o'rniga qo'yiladi.</i>"
        )
        return
    date_part, msg_part = args.split("|", 1)
    date_part = date_part.strip()
    msg_part = msg_part.strip()
    try:
        datetime.strptime(date_part, "%d.%m.%Y")
    except Exception:
        await send_text(bot, message, conn_id, "<b>Sana formati xato!</b> (Kun.Oy.Yil bo'lishi kerak)")
        return
    save_timer_config(date_part, msg_part)
    await send_text(bot, message, conn_id, f"{CHECK} <b>Timer sozlamalari saqlandi!</b>\n📅 Sana: <code>{date_part}</code>")


# ─────────────────────────────────────────────────────────────
# READ FILE  (.rf [sahifa] — faylga reply)
# ─────────────────────────────────────────────────────────────

FILE_CACHE = {}

async def _show_file_page(bot, message, conn_id, chat_key, index):
    data = FILE_CACHE[chat_key]
    chunks = data["chunks"]
    total = len(chunks)
    index = max(0, min(index, total - 1))
    text = (
        f"✅ <b>Fayl:</b> <code>{data['name']}</code>\n"
        f"📒 <b>Sahifa: {index + 1}/{total}</b> | <b>Hajmi: {data['size']}</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"<pre>{chunks[index]}</pre>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💡 <i>Keyingi sahifa uchun:</i> <code>.rf {index + 2}</code>"
    )
    await send_text(bot, message, conn_id, text)


async def cmd_read_file(bot, message, conn_id, args):
    chat_key = message.chat.id
    page_arg = args.strip()
    if page_arg.isdigit() and chat_key in FILE_CACHE:
        await _show_file_page(bot, message, conn_id, chat_key, int(page_arg) - 1)
        return
    reply = message.reply_to_message
    if not reply or not reply.document:
        await send_text(bot, message, conn_id, f"{ERROR} <b>Faylga reply qiling (masalan .txt)!</b>")
        return
    await send_typing(bot, message, conn_id)
    try:
        file_info = await bot.get_file(reply.document.file_id)
        fb = await bot.download_file(file_info.file_path)
        content = fb.read().decode("utf-8", errors="replace")
        chunks = [content[i:i + 1500] for i in range(0, len(content), 1500)]
        if not chunks:
            chunks = [""]
        FILE_CACHE[chat_key] = {
            "chunks": chunks,
            "name": reply.document.file_name or "fayl.txt",
            "size": f"{getattr(file_info, 'file_size', 0)} bayt"
        }
        await _show_file_page(bot, message, conn_id, chat_key, 0)
    except Exception as e:
        await send_text(bot, message, conn_id, f"{ERROR} <b>Faylni o'qishda xato:</b> <code>{e}</code>")


# ─────────────────────────────────────────────────────────────
# FILE UPLOADERS  (.catbox .envs .kappa .oxo .0x0 .x0 .tmpfiles .pomf .bash)
# ─────────────────────────────────────────────────────────────

async def _get_upload_source(bot, message):
    reply = message.reply_to_message
    if not reply:
        return None
    try:
        if reply.document:
            file_info = await bot.get_file(reply.document.file_id)
            fb = await bot.download_file(file_info.file_path)
            return fb.read(), reply.document.file_name or "file.bin"
        if reply.photo:
            file_info = await bot.get_file(reply.photo[-1].file_id)
            fb = await bot.download_file(file_info.file_path)
            return fb.read(), f"photo_{reply.message_id}.jpg"
        if reply.voice:
            file_info = await bot.get_file(reply.voice.file_id)
            fb = await bot.download_file(file_info.file_path)
            return fb.read(), "voice.ogg"
        if reply.text:
            return reply.text.encode("utf-8"), "text.txt"
    except Exception:
        return None
    return None


async def _upload_to_service(service, data, name):
    form = aiohttp.FormData()
    async with aiohttp.ClientSession() as session:
        if service == "catbox":
            form.add_field("reqtype", "fileupload")
            form.add_field("fileToUpload", data, filename=name, content_type="application/octet-stream")
            async with session.post("https://catbox.moe/user/api.php", data=form, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                resp.raise_for_status()
                return (await resp.text()).strip()
        if service == "envs":
            form.add_field("file", data, filename=name, content_type="application/octet-stream")
            async with session.post("https://envs.sh", data=form, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                resp.raise_for_status()
                return (await resp.text()).strip()
        if service == "kappa":
            form.add_field("file", data, filename=name, content_type="application/octet-stream")
            async with session.post("https://kappa.lol/api/upload", data=form, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                resp.raise_for_status()
                j = await resp.json(content_type=None)
                return f"https://kappa.lol/{j['id']}"
        if service == "0x0":
            form.add_field("file", data, filename=name, content_type="application/octet-stream")
            form.add_field("secret", "true")
            async with session.post("https://0x0.st", data=form, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                resp.raise_for_status()
                return (await resp.text()).strip()
        if service == "x0":
            form.add_field("file", data, filename=name, content_type="application/octet-stream")
            async with session.post("https://x0.at", data=form, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                resp.raise_for_status()
                return (await resp.text()).strip()
        if service == "tmpfiles":
            form.add_field("file", data, filename=name, content_type="application/octet-stream")
            async with session.post("https://tmpfiles.org/api/v1/upload", data=form, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                resp.raise_for_status()
                j = await resp.json(content_type=None)
                return j["data"]["url"]
        if service == "pomf":
            form.add_field("files[]", data, filename=name, content_type="application/octet-stream")
            async with session.post("https://pomf.lain.la/upload.php", data=form, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                resp.raise_for_status()
                j = await resp.json(content_type=None)
                return j["files"][0]["url"]
        if service == "bash":
            async with session.put("https://bashupload.com", data=data, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                resp.raise_for_status()
                text = await resp.text()
                for line in text.splitlines():
                    if "wget" in line:
                        return line.split()[-1]
                return "Topilmadi"
    return "Noma'lum xato"


async def cmd_upload(bot, message, conn_id, args, service):
    src = await _get_upload_source(bot, message)
    if not src:
        await send_text(bot, message, conn_id, f"{ERROR} <b>Faylga reply qiling!</b>\n\n<blockquote>Namuna: <code>.catbox</code> (faylga reply qilib)</blockquote>")
        return
    data, name = src
    await send_typing(bot, message, conn_id)
    try:
        url = await _upload_to_service(service, data, name)
        await send_text(bot, message, conn_id, f"{CHECK} <b>Fayl yuklandi!</b>\n\n📄 <b>Link:</b> <code>{url}</code>")
    except Exception as e:
        await send_text(bot, message, conn_id, f"{ERROR} <b>Xato:</b> <code>{e}</code>")


# ─────────────────────────────────────────────────────────────
# RANDOM MEME  (.meme / .rmeme)
# ─────────────────────────────────────────────────────────────

async def cmd_random_meme(bot, message, conn_id, args):
    await send_typing(bot, message, conn_id)
    try:
        data = await http_get_json("https://meme-api.com/gimme", timeout=20)
        url = data.get("url")
        if not url:
            await send_text(bot, message, conn_id, f"{ERROR} <b>Mem topishda xatolik yuz berdi!</b>")
            return
        title = data.get("title", "")
        img = await http_get_bytes(url, timeout=30)
        caption = f"{CHECK} <b>Marhamat, tasodifiy mem!</b>"
        if title:
            caption += f"\n\n💬 <code>{title}</code>"
        await bot.send_photo(
            chat_id=message.chat.id,
            photo=types.BufferedInputFile(img, filename="meme.jpg"),
            caption=caption,
            business_connection_id=conn_id,
        )
    except Exception as e:
        await send_text(bot, message, conn_id, f"{ERROR} <b>Mem xatosi:</b> <code>{e}</code>")


# ─────────────────────────────────────────────────────────────
# PROFILE CLOCK  (.soat on|off / .soatbio on|off)
# ─────────────────────────────────────────────────────────────

async def cmd_soat(bot, message, conn_id, args):
    mode = args.strip().lower()
    conn = get_conn_settings(conn_id)
    if mode not in ("on", "off"):
        await send_text(bot, message, conn_id, f"{ERROR} <b>Xato ishlatish!</b>\n\n<blockquote>Namuna: <code>.soat on</code> yoki <code>.soat off</code></blockquote>")
        return
    if mode == "on":
        if conn.get("clock"):
            await send_text(bot, message, conn_id, "<b>Ismdagi soat allaqachon yoqilgan!</b>")
            return
        set_conn_setting(conn_id, clock=True,
                         orig_first_name=conn.get("first_name") or "",
                         orig_last_name=conn.get("last_name") or "")
        await send_text(bot, message, conn_id, f"{CHECK} <b>Ismdagi soat yoqildi!</b>")
    else:
        set_conn_setting(conn_id, clock=False)
        orig_f = conn.get("orig_first_name") or conn.get("first_name") or "User"
        orig_l = conn.get("orig_last_name") or conn.get("last_name") or ""
        try:
            await bot.set_business_account_name(business_connection_id=conn_id, first_name=orig_f, last_name=orig_l)
        except Exception as e:
            logger.warning(f"soat off restore failed: {e}")
        await send_text(bot, message, conn_id, f"{CHECK} <b>Ismdagi soat o'chirildi va ism qaytarildi.</b>")


async def cmd_soatbio(bot, message, conn_id, args):
    mode = args.strip().lower()
    conn = get_conn_settings(conn_id)
    if mode not in ("on", "off"):
        await send_text(bot, message, conn_id, f"{ERROR} <b>Xato ishlatish!</b>\n\n<blockquote>Namuna: <code>.soatbio on</code> yoki <code>.soatbio off</code></blockquote>")
        return
    if mode == "on":
        if conn.get("clock_bio"):
            await send_text(bot, message, conn_id, "<b>Biodagi soat allaqachon yoqilgan!</b>")
            return
        set_conn_setting(conn_id, clock_bio=True)
        try:
            if hasattr(bot, "set_business_account_bio"):
                from storage import to_bold_time
                bio = f"🕒 Soat: {to_bold_time(datetime.now(UZB_TZ).strftime('%H:%M'))} | 📅 Sana: {datetime.now(UZB_TZ).strftime('%d.%m.%Y')}"
                await bot.set_business_account_bio(business_connection_id=conn_id, bio=bio)
        except Exception:
            pass
        await send_text(bot, message, conn_id, f"{CHECK} <b>Biodagi soat yoqildi!</b>")
    else:
        set_conn_setting(conn_id, clock_bio=False)
        try:
            if hasattr(bot, "set_business_account_bio"):
                await bot.set_business_account_bio(business_connection_id=conn_id, bio=conn.get("orig_bio") or "")
        except Exception:
            pass
        await send_text(bot, message, conn_id, f"{CHECK} <b>Biodagi soat o'chirildi va bio qaytarildi.</b>")


# ─────────────────────────────────────────────────────────────
# AUTO AD  (.auto <link> <interval> | <xabar> / .stopauto <link>)
# ─────────────────────────────────────────────────────────────

AD_TASKS = {}

async def cmd_auto(bot, message, conn_id, args):
    args_s = args.strip()
    try:
        if "|" not in args_s:
            raise ValueError
        part1, ad_msg = args_s.split("|", 1)
        p = part1.strip().split()
        if len(p) < 2:
            raise ValueError
        link = p[0]
        interval = int(p[1])
        ad_msg = ad_msg.strip()
        if interval < 10:
            await send_text(bot, message, conn_id, f"{ERROR} <b>Vaqt kamida 10 soniya bo'lishi kerak!</b>")
            return
    except (ValueError, IndexError):
        await send_text(
            bot, message, conn_id,
            f"{ERROR} <b>Xato ishlatish!</b>\n\n"
            f"📝 <b>Namuna:</b>\n"
            f"<code>.auto @guruhlink 60 | Sotiladi iPhone 15!</code>\n\n"
            f"☝️ <i>Link va vaqtdan keyin '|' belgisini qo'ying!</i>"
        )
        return

    key = (conn_id, link)
    if key in AD_TASKS:
        AD_TASKS[key].cancel()

    async def ad_loop():
        while True:
            try:
                await bot.send_message(chat_id=link, text=ad_msg, business_connection_id=conn_id)
            except Exception as e:
                logger.warning(f"Auto ad send failed for {link}: {e}")
            await asyncio.sleep(interval)

    AD_TASKS[key] = asyncio.create_task(ad_loop())
    await send_text(
        bot, message, conn_id,
        f"{CHECK} <b>Auto-reklama yoqildi!</b>\n\n"
        f"👥 <b>Guruh:</b> <code>{link}</code>\n"
        f"⏳ <b>Interval:</b> <code>{interval}</code> soniya\n"
        f"📝 <b>Xabar:</b> <i>{ad_msg[:50]}</i>\n\n"
        f"To'xtatish uchun: <code>.stopauto {link}</code>"
    )


async def cmd_stopauto(bot, message, conn_id, args):
    link = args.strip()
    key = (conn_id, link)
    if key in AD_TASKS:
        AD_TASKS[key].cancel()
        del AD_TASKS[key]
        await send_text(bot, message, conn_id, f"{CHECK} <b>{link} uchun auto-reklama to'xtatildi!</b>")
    else:
        await send_text(bot, message, conn_id, f"{ERROR} <b>Bu guruhda faol reklama topilmadi.</b>")


# ─────────────────────────────────────────────────────────────
# FUN / COMMAND LIST  (.fun .co .komandalar)
# ─────────────────────────────────────────────────────────────

FUN_LIST_TEXT = """✅ <b>🎭 Animatsiyalar:</b>
<code>.love</code>, <code>.yurak</code>, <code>.police</code>, <code>.fuck</code>, <code>.kill</code>, <code>.ari</code>, <code>.load</code>, <code>.god</code>, <code>.snake</code>, <code>.ghost</code>, <code>.cosmo</code>, <code>.dance</code>, <code>.knife</code>, <code>.chaqmoq</code>, <code>.home</code>, <code>.ayriliq</code>, <code>.money</code>, <code>.search</code>, <code>.snow</code>, <code>.xd</code>

🌀 <b>RolePlay:</b>
<code>.me</code> - Birinchi shaxs nomidan
<code>.do</code> - Atrofdagi voqea
<code>.try</code> - Omadingizni sinash
<code>.todo</code> - Fraza va harakat

📂 <b>Modullar:</b>
<code>.acc</code> - Akkunt haqida ma'lumot
<code>.ai</code> - Sun'iy intellekt
<code>.grok</code> - Grok AI
<code>.r</code> - Stiker yasash (reply)
<code>.rf</code> - Faylni o'qish (reply)
<code>.gender</code> - Jinsni aniqlash
<code>.ro</code> - Rus ruletkasi
<code>.shlink</code> - Linkni qisqartirish
<code>.yt</code> - YouTube qidiruv
<code>.t2s</code> - Matnni ovoz qilish
<code>.tr</code> - Tarjimon
<code>.kurs</code> - Valyuta kurslari
<code>.q</code> - Xabarni stiker qilish (reply)
<code>.telegraph</code> - Telegraph maqola
<code>.rmeme</code> - Tasodifiy memlar
<code>.catbox</code> - Fayl yuklash
<code>.weather</code> - Havo
<code>.lyrics</code> - Qo'shiq matni
<code>.soat</code>, <code>.soatbio</code> - Profil soati
<code>.time</code>, <code>.settime</code> - Timer

<b>AnimeTools:</b>
<code>.aq</code> - Anime sitatalari
<code>.ra</code> - Tasodifiy anime
<code>.art</code> - Anime surat

<code>.getid</code> - Premium emoji ID"""

async def cmd_fun_list(bot, message, conn_id, args):
    await send_text(bot, message, conn_id, FUN_LIST_TEXT)
