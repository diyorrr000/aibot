from telethon import events, utils
import os

async def setup_downloader(client):
    @client.on(events.NewMessage(pattern=r'\.x(?: (.*))?', outgoing=True))
    async def down_msg_handler(event):
        """Kanalda cheklangan xabarlarni ko'chirib olish"""
        link_str = event.pattern_match.group(1)
        if not link_str:
            await event.edit("🚫 <b>Link kiriting!</b>\n\n<blockquote>Namuna: <code>.x https://t.me/kanal/123</code></blockquote>", parse_mode='html')
            return
            
        link = link_str.split('?')[0] # Parametrlarni olib tashlash
        
        try:
            if 't.me/c/' in link:
                # Yopiq kanal linki: https://t.me/c/12345678/90
                parts = link.split('/')
                msg_id = int(parts[-1])
                chat_id = int(parts[-2])
                # Telethon yopiq kanallarni -100 prefiksi bilan taniydi
                peer = int(f"-100{chat_id}")
            elif 't.me/' in link:
                # Ochiq kanal linki: https://t.me/channel/90
                parts = link.split('/')
                msg_id = int(parts[-1])
                peer = parts[-2]
            else:
                await event.edit("🚫 <b>Link noto'g'ri ko'rinishda!</b>", parse_mode='html')
                return
        except Exception:
            await event.edit("🚫 <b>Linkdan ma'lumotni ajratib bo'lmadi!</b>", parse_mode='html')
            return

        await event.edit("✅ <b>Yuklanmoqda...</b>", parse_mode='html')
        
        try:
            # Xabarni olish
            msg = await client.get_messages(peer, ids=msg_id)
            if not msg:
                await event.edit("🚫 <b>Xabar topilmadi!</b>", parse_mode='html')
                return

            caption = msg.message
            file_path = None
            
            if msg.media:
                # Medianı yuklab olish
                file_path = await client.download_media(msg)
                
                # Medianı yuborish
                await client.send_file(
                    event.chat_id,
                    file_path,
                    caption=caption,
                    entities=msg.entities,
                    reply_to=event.reply_to_msg_id
                )
                
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
            else:
                # Faqat matnli xabar bo'lsa
                await client.send_message(
                    event.chat_id,
                    caption,
                    entities=msg.entities,
                    reply_to=event.reply_to_msg_id
                )

            await event.delete()
            
        except Exception as e:
            await event.edit(f"🚫 <b>Xatolik yuz berdi:</b>\n<code>{e}</code>", parse_mode='html')
            if 'file_path' in locals() and file_path and os.path.exists(file_path):
                os.remove(file_path)
