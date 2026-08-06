from telethon import events
import requests
import io

CHECK_EMOJI = "✅"

async def setup_quote(client):
    @client.on(events.NewMessage(pattern=r'\.q(?: (.*))?', outgoing=True))
    async def quote_handler(event):
        """Xabarni stiker (quote) ko'rinishiga keltirish"""
        reply = await event.get_reply_message()
        if not reply or not (reply.text or reply.caption):
            await event.edit("<b>Matnli xabarga reply qiling!</b>\n\n📝 <b>Namuna:</b> <code>.q</code> (xabarga reply qilib)")
            return

        await event.edit(f"{CHECK_EMOJI} <b>Quote tayyorlanmoqda...</b>", parse_mode='html')
        
        try:
            # Quotly API
            sender = await reply.get_sender()
            first_name = sender.first_name if hasattr(sender, 'first_name') else "Noma'lum"
            last_name = sender.last_name if hasattr(sender, 'last_name') else ""
            username = sender.username if hasattr(sender, 'username') else ""
            user_id = sender.id
            
            # Avatar olishga harakat qilish
            avatar_url = ""
            async for photo in client.iter_profile_photos(user_id, limit=1):
                avatar_file = await client.download_media(photo, bytes)
                # Bu yerda Quotly avatar uchun link so'raydi, lekin biz bazaviy API-dan foydalanamiz
                break

            json_data = {
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
                            "first_name": first_name,
                            "last_name": last_name,
                            "username": username,
                            "language_code": "uz"
                        },
                        "text": reply.raw_text,
                        "replyMessage": {}
                    }
                ]
            }

            response = requests.post("https://bot.lyo.su/quoteit/generate", json=json_data, timeout=30)
            if response.status_code == 200:
                sticker_data = io.BytesIO(response.content)
                sticker_data.name = "quote.webp"
                
                await client.send_file(
                    event.chat_id,
                    sticker_data,
                    reply_to=reply.id
                )
                await event.delete()
            else:
                await event.edit(f"<b>Quote API xatosi: {response.status_code}</b>")
        except Exception as e:
            await event.edit(f"<b>Xatolik:</b> <code>{str(e)}</code>")
