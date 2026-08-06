from telethon import events, types
import requests

CHECK_EMOJI = "✅"

async def setup_lyrics(client):
    @client.on(events.NewMessage(pattern=r'\.lyrics(?: (.*))?', outgoing=True))
    async def lyrics_handler(event):
        """Musiqa matnini Genius dan qidirish"""
        args = event.pattern_match.group(1)
        reply = await event.get_reply_message()
        
        song = ""
        if args:
            song = args.strip()
        elif reply and reply.audio:
            # Agar audiodan performer va sarlavhani olish imkoni bo'lsa
            attr = next((a for a in reply.document.attributes if isinstance(a, types.DocumentAttributeAudio)), None)
            if attr:
                performer = attr.performer or "Noma'lum"
                title = attr.title or "Noma'lum"
                song = f"{performer} - {title}"
        
        if not song:
            await event.edit(
                "<b>Xato ishlatish!</b>\n\n"
                f"📝 <b>Namuna:</b>\n"
                f"1. <code>.lyrics Uzmir & Zilola - Ota</code>\n"
                f"2. Musiqaga reply qilib <code>.lyrics</code> deb yozing.",
                parse_mode='html'
            )
            return

        await event.edit(f"{CHECK_EMOJI} <b>`{song}` matni qidirilmoqda...</b>", parse_mode='html')

        try:
            # Hozirda barqaror ishlaydigan bepul Lyrics API
            # https://lyrist.vercel.app/api/:song
            response = requests.get(f"https://lyrist.vercel.app/api/{song}", timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data or not data.get("lyrics"):
                    await event.edit(f"<b>Afsuski, `{song}` uchun matn topilmadi.</b>")
                    return
                
                title = data.get("title", song)
                artist = data.get("artist", "")
                lyrics = data.get("lyrics", "")
                
                # Matn juda uzun bo'lsa, uni bo'laklarga ajratish yoki qisqartirish kerak
                # Telegram bitta xabarda 4096 belgi qabul qiladi
                if len(lyrics) > 3500:
                    lyrics = lyrics[:3500] + "..."

                output = (
                    f"📝 <b>Musiqa matni:</b>\n"
                    f"🎵 <b>Nomi:</b> <code>{title}</code>\n"
                    f"👤 <b>Ijrochi:</b> <code>{artist}</code>\n\n"
                    f"<blockquote>{lyrics}</blockquote>"
                )
                await event.edit(output, parse_mode='html')
            else:
                await event.edit("<b>Serverda xatolik yuz berdi.</b>")
        except Exception as e:
            await event.edit(f"<b>Xatolik:</b> <code>{str(e)}</code>")
