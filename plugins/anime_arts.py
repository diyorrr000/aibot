from telethon import events
import requests

CHECK_EMOJI = "✅"
ERROR_EMOJI = "❌"
ANIME_EMOJI = "🍿"

async def get_anime_art(category="sfw"):
    try:
        url = f"https://api.waifu.pics/{category}/waifu"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            return r.json().get("url")
    except:
        pass
    return None

async def setup_anime_arts(client):
    @client.on(events.NewMessage(pattern=r'\.art', outgoing=True))
    async def art_handler(event):
        """Yoqimli anime suratlari"""
        await event.edit(f"{CHECK_EMOJI} <b>Anime surat yuklanmoqda...</b>")
        
        img_url = await get_anime_art("sfw")
        if img_url:
            await client.send_file(
                event.chat_id, 
                img_url, 
                caption=f"{ANIME_EMOJI} <b>Yoqimli anime surat!</b>", 
                reply_to=event.reply_to_msg_id
            )
            await event.delete()
        else:
            await event.edit(f"{ERROR_EMOJI} <b>Surat yuklashda xatolik!</b>")

    @client.on(events.NewMessage(pattern=r'\.nsfwart', outgoing=True))
    async def nsfw_art_handler(event):
        """NSFW anime suratlari"""
        await event.edit(f"{CHECK_EMOJI} <b>NSFW surat yuklanmoqda...</b>")
        
        img_url = await get_anime_art("nsfw")
        if img_url:
            await client.send_file(
                event.chat_id, 
                img_url, 
                caption=f"{ANIME_EMOJI} <b>NSFW anime surat!</b>", 
                reply_to=event.reply_to_msg_id
            )
            await event.delete()
        else:
            await event.edit(f"{ERROR_EMOJI} <b>Surat yuklashda xatolik!</b>")
