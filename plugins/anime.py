from telethon import events
import requests
import os
import mimetypes
import urllib.parse

CHECK_EMOJI = "✅"
ERROR_EMOJI = "❌"
ANIME_EMOJI = "🍿"

async def translate_text(text, target_lang="uz"):
    if not text: return ""
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t&q={urllib.parse.quote(text)}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            result = response.json()
            return "".join([part[0] for part in result[0]])
    except:
        pass
    return text

async def setup_anime(client):
    @client.on(events.NewMessage(pattern=r'\.(?:findanime|fa)', outgoing=True))
    async def findanime_handler(event):
        """Rasm orqali qaysi anime ekanligini topish"""
        reply = await event.get_reply_message()
        msg = reply if reply else event.message
        
        if not msg.media:
            await event.edit("<b>Rasm yoki videoga reply qiling!</b>")
            return

        await event.edit(f"{CHECK_EMOJI} <b>Anime qidirilmoqda...</b>")
        
        file_path = None
        try:
            # Faylni yuklab olish
            file_path = await client.download_media(msg)
            
            with open(file_path, "rb") as f:
                r = requests.post(
                    "https://api.trace.moe/search",
                    files={"image": f},
                    timeout=30
                )
            
            if r.status_code != 200:
                await event.edit(f"<b>API xatosi: {r.status_code}</b>")
                return

            data = r.json()
            if not data.get("result"):
                await event.edit("<b>Hech narsa topilmadi.</b>")
                return

            res = data['result'][0]
            episode = res.get('episode', 'Noma\'lum')
            video_url = res.get('video')
            filename = res.get('filename', 'Noma\'lum')
            similarity = round(res.get('similarity', 0) * 100, 2)
            
            caption = (
                f"{ANIME_EMOJI} <b>Anime topildi!</b>\n\n"
                f"🎬 <b>Nomi:</b> <code>{filename}</code>\n"
                f"🍿 <b>Qism:</b> <code>{episode}</code>\n"
                f"🤨 <b>O'xshashlik:</b> <code>{similarity}%</code>"
            )
            
            await client.send_file(
                event.chat_id,
                video_url or file_path,
                caption=caption,
                reply_to=reply.id if reply else None,
                parse_mode='html'
            )
            await event.delete()
                
        except Exception as e:
            await event.edit(f"<b>Xatolik yuz berdi!</b>")
        finally:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)

    @client.on(events.NewMessage(pattern=r'\.(?:animequote|aq)(?: (.*))?', outgoing=True))
    async def anime_quote_handler(event):
        """Tasodifiy anime sitatasi"""
        args = event.pattern_match.group(1)
        await event.edit(f"{CHECK_EMOJI} <b>Sitat qidirilmoqda...</b>")
        
        try:
            url = "https://animechan.xyz/api/random"
            if args:
                url = f"https://animechan.xyz/api/random/anime?title={urllib.parse.quote(args)}"
            
            r = requests.get(url, timeout=15)
            if r.status_code != 200:
                await event.edit("<b>Ma'lumot topilmadi.</b>")
                return
                
            data = r.json()
            quote = await translate_text(data["quote"])
            character = data["character"]
            anime = data["anime"]
            
            output = (
                f"{ANIME_EMOJI} <b>Anime Sitatasi:</b>\n\n"
                f"<blockquote>{quote}</blockquote>\n"
                f"👤 <b>Qahramon:</b> <code>{character}</code>\n"
                f"🎬 <b>Anime:</b> <code>{anime}</code>"
            )
            await event.edit(output, parse_mode='html')
            
        except Exception:
            await event.edit("<b>Sitat topishda xatolik yuz berdi.</b>")

    @client.on(events.NewMessage(pattern=r'\.(?:randomanime|ra)', outgoing=True))
    async def random_anime_handler(event):
        """Tasodifiy anime tavsiyasi"""
        await event.edit(f"{CHECK_EMOJI} <b>Tasodifiy anime tanlanmoqda...</b>")
        
        try:
            # Shikimori API (yaxshiroq va barqarorroq)
            r = requests.get("https://shikimori.one/api/animes?limit=1&order=random", timeout=15)
            if r.status_code != 200:
                await event.edit("<b>API xatosi (Shikimori).</b>")
                return
            
            data = r.json()[0]
            title = data.get("name")
            russian_title = data.get("russian")
            score = data.get("score")
            episodes = data.get("episodes")
            kind = data.get("kind")
            img = f"https://shikimori.one{data['image']['original']}"
            
            # Qo'shimcha ma'lumot olish (description uchun)
            anime_id = data["id"]
            r_full = requests.get(f"https://shikimori.one/api/animes/{anime_id}", timeout=15).json()
            desc = r_full.get("description") or "Tavsif yo'q."
            
            # Tarjima qilish
            uz_desc = await translate_text(desc)
            if len(uz_desc) > 800: uz_desc = uz_desc[:800] + "..."
            
            caption = (
                f"{ANIME_EMOJI} <b>Tasodifiy Anime:</b>\n\n"
                f"🎬 <b>Nomi:</b> <code>{russian_title or title}</code>\n"
                f"⭐ <b>Reyting:</b> <code>{score}</code>\n"
                f"📦 <b>Turi:</b> <code>{kind}</code> | 📺 <b>Qismlar:</b> <code>{episodes}</code>\n\n"
                f"📖 <b>Tavsif:</b> <i>{uz_desc}</i>"
            )
            
            await client.send_file(event.chat_id, img, caption=caption, parse_mode='html')
            await event.delete()
            
        except Exception:
            await event.edit("<b>Anime tanlashda xatolik yuz berdi.</b>")
