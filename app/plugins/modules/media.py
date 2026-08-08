import urllib.parse
import re
import random
import aiohttp
from aiogram import Bot, types
from aiogram.enums import ChatAction

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

async def cmd_yt(bot: Bot, message: types.Message, conn_id: str, args: str):
    query = args.strip()
    if not query:
        await send_fb(bot, message, conn_id, "🚫 <b>YouTube qidiruv matnini kiriting!</b> Misol: <code>.yt O'zbekiston</code>")
        return
    await send_typing(bot, message, conn_id)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://www.youtube.com/results", params={"search_query": query}, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                html = (await resp.read()).decode("utf-8", errors="ignore")
                video_ids = re.findall(r"watch\?v=(\S{11})", html)
                if not video_ids:
                    await send_fb(bot, message, conn_id, "🚫 <b>Topilmadi.</b>")
                    return
                video_url = f"https://www.youtube.com/watch?v={video_ids[0]}"
                await send_fb(bot, message, conn_id, f"▶️ <b>YouTube Natijasi:</b>\n🔗 {video_url}")
    except Exception as e:
        await send_fb(bot, message, conn_id, f"🚫 <b>YouTube xatosi:</b> <code>{e}</code>")

async def cmd_anime(bot: Bot, message: types.Message, conn_id: str, args: str):
    await send_typing(bot, message, conn_id)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://shikimori.one/api/animes?limit=1&order=random", timeout=aiohttp.ClientTimeout(total=15)) as resp:
                data = await resp.json(content_type=None)
                anime = data[0]
                title = anime.get("russian") or anime.get("name")
                score = anime.get("score")
                text = f"🍿 <b>Tasodifiy Anime:</b> <code>{title}</code>\n⭐ Reyting: <code>{score}</code>"
                await send_fb(bot, message, conn_id, text)
    except Exception as e:
        await send_fb(bot, message, conn_id, f"🚫 <b>Anime xatosi:</b> <code>{e}</code>")

async def cmd_meme(bot: Bot, message: types.Message, conn_id: str, args: str):
    await send_typing(bot, message, conn_id)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://meme-api.com/gimme", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    img_url = data.get("url")
                    title = data.get("title", "Meme")
                    if img_url:
                        try:
                            await bot.send_photo(chat_id=message.chat.id, photo=img_url, caption=f"😂 <b>{title}</b>", business_connection_id=conn_id)
                        except Exception:
                            await bot.send_photo(chat_id=message.chat.id, photo=img_url, caption=f"😂 <b>{title}</b>")
                        return
    except Exception:
        pass

    fallback_memes = [
        "😂 Dasturchi: 'Kod mening kompyuterimda ishlayapti!'\nQA: 'Biz mijozlarga sening kompyuteringni sotmaymiz!'",
        "🤣 'Bug' emas, bu hujjatlashtirilmagan funksiya!",
        "🤖 AI: 'Men insoniyat o'rnini egallayman'\nInson: '.help qanday ishlaydi?'\nAI: 'Kechirasiz...'",
    ]
    await send_fb(bot, message, conn_id, f"😂 <b>Random Meme:</b>\n\n{random.choice(fallback_memes)}")

def register(pm):
    pm.register_command(".yt", cmd_yt)
    pm.register_command(".anime", cmd_anime)
    pm.register_command(".ra", cmd_anime)
    pm.register_command(".meme", cmd_meme)
    pm.register_command(".rmeme", cmd_meme)
