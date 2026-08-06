"""
Aiogram-based implementation of all userbot plugin commands.

These commands work inside ANY chat through the Telegram Business API
(business_connection_id). No Telethon session is required — everything
is done via the bot (aiogram) + public HTTP APIs.

Every command handler signature:
    async def cmd_xxx(bot: Bot, message: types.Message, conn_id: str, args: str) -> None
"""
import asyncio
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
    await bot.send_message(
        chat_id=message.chat.id,
        text=text,
        business_connection_id=conn_id,
        parse_mode=parse_mode,
    )


async def send_typing(bot: Bot, message: types.Message, conn_id: str):
    try:
        await bot.send_chat_action(
            chat_id=message.chat.id,
            action=ChatAction.TYPING,
            business_connection_id=conn_id,
        )
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
    try:
        url = "https://animechan.xyz/api/random"
        if args.strip():
            url = f"https://animechan.xyz/api/random/anime?title={urllib.parse.quote(args.strip())}"
        data = await http_get_json(url)
        quote = data.get("quote", "")
        character = data.get("character", "")
        anime = data.get("anime", "")
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
    except Exception as e:
        await send_text(bot, message, conn_id, f"{ERROR} <b>Sitat topishda xatolik:</b> <code>{e}</code>")


# ─────────────────────────────────────────────────────────────
# ANIME ART  (.art)
# ─────────────────────────────────────────────────────────────

async def cmd_anime_art(bot, message, conn_id, args):
    await send_typing(bot, message, conn_id)
    try:
        data = await http_get_json("https://api.waifu.pics/sfw/waifu")
        img_url = data.get("url")
        if not img_url:
            await send_text(bot, message, conn_id, f"{ERROR} <b>Surat topilmadi.</b>")
            return
        img = await http_get_bytes(img_url)
        await bot.send_photo(
            chat_id=message.chat.id,
            photo=types.BufferedInputFile(img, filename="anime.jpg"),
            caption=f"🍿 <b>Yoqimli anime surat!</b>",
            business_connection_id=conn_id,
        )
    except Exception as e:
        await send_text(bot, message, conn_id, f"{ERROR} <b>Xatolik:</b> <code>{e}</code>")
