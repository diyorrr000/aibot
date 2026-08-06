from telethon import events
import requests
import io
import re

CHECK_EMOJI = "✅"
ERROR_EMOJI = "🚫"

async def setup_yt_search(client):
    @client.on(events.NewMessage(pattern=r'\.(?:yt|ytsearch)(?: (.*))?', outgoing=True))
    async def yt_search_handler(event):
        """YouTube dan video qidirish"""
        query = event.pattern_match.group(1)
        if not query:
            await event.edit(f"{ERROR_EMOJI} <b>Qidiruv matnini kiriting!</b>\n\n<blockquote>Namuna: <code>.yt O'zbekiston</code></blockquote>", parse_mode='html')
            return
        
        query = query.strip()
        await event.edit(f"{CHECK_EMOJI} <b>YouTube dan qidirilmoqda...</b>", parse_mode='html')
        
        try:
            # YouTube qidiruv sahifasini olish
            search_url = f"https://www.youtube.com/results?search_query={query}"
            response = requests.get(search_url, timeout=15)
            html = response.text
            
            # Video ID larini ajratib olish
            video_ids = re.findall(r"watch\?v=(\S{11})", html)
            
            if not video_ids:
                await event.edit(f"{ERROR_EMOJI} <b>YouTube dan hech narsa topilmadi.</b>", parse_mode='html')
                return
                
            video_id = video_ids[0]
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            # Video ma'lumotlarini olish
            api_url = f"https://noembed.com/embed?url={video_url}"
            video_info = requests.get(api_url).json()
            
            title = video_info.get("title", "Nomsiz video")
            author = video_info.get("author_name", "Noma'lum muallif")
            
            # Preview (thumbnail) rasmni olish
            thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
            thumb_res = requests.get(thumbnail_url)
            if thumb_res.status_code == 404:
                thumbnail_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
                thumb_res = requests.get(thumbnail_url)
            
            thumb_file = io.BytesIO(thumb_res.content)
            thumb_file.name = "thumb.jpg"
            
            caption = (
                f"{CHECK_EMOJI} <b>YouTube Qidiruv Natijasi:</b>\n\n"
                f"💻 <b>Nomi:</b> <code>{title}</code>\n"
                f"👤 <b>Kanal:</b> <code>{author}</code>\n\n"
                f"🔗 <b>Havola:</b> {video_url}"
            )
            
            await client.send_file(
                event.chat_id,
                thumb_file,
                caption=caption,
                parse_mode='html',
                reply_to=event.reply_to_msg_id
            )
            await event.delete()
            
        except Exception as e:
            await event.edit(f"{ERROR_EMOJI} <b>YouTube xatosi:</b> <code>{str(e)}</code>", parse_mode='html')
