from telethon import events, utils
import os

# Fayl sahifalarini saqlash uchun kesh
FILE_CACHE = {} # {chat_id: {"chunks": [], "name": "", "size": ""}}

async def setup_read_file(client):
    @client.on(events.NewMessage(pattern=r'\.rf(?: (\d+))?', outgoing=True))
    async def read_file_handler(event):
        """Faylni o'qish va sahifalarga bo'lish"""
        page_arg = event.pattern_match.group(1)
        
        # Agar sahifa raqami berilgan bo'lsa va keshda fayl bo'lsa
        if page_arg and event.chat_id in FILE_CACHE:
            await show_page(event, int(page_arg) - 1)
            return

        reply = await event.get_reply_message()
        if not reply or not reply.file:
            await event.edit("🚫 <b>Faylga reply qiling (masalan .txt)!</b>", parse_mode='html')
            return

        await event.edit("✅ <b>Fayl yuklanmoqda...</b>", parse_mode='html')
        
        file_path = await reply.download_media()
        try:
            # Faylni o'qish
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Fayl ma'lumotlarini saqlash
            chunks = [content[i:i + 1500] for i in range(0, len(content), 1500)]
            FILE_CACHE[event.chat_id] = {
                "chunks": chunks,
                "name": os.path.basename(file_path),
                "size": f"{os.path.getsize(file_path)} bayt"
            }
            
            # Faylni o'chirish
            os.remove(file_path)
            
            await show_page(event, 0)
            
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            await event.edit(f"🚫 <b>Faylni o'qishda xato:</b> <code>{e}</code>", parse_mode='html')

async def show_page(event, index):
    chat_id = event.chat_id
    if chat_id not in FILE_CACHE:
        return

    data = FILE_CACHE[chat_id]
    chunks = data["chunks"]
    total = len(chunks)
    
    # Indeksni chegaralash
    index = max(0, min(index, total - 1))
    
    text = f"✅ <b>Fayl:</b> <code>{data['name']}</code>\n"
    text += f"📒 <b>Sahifa: {index + 1}/{total}</b> | <b>Hajmi: {data['size']}</b>\n"
    text += f"━━━━━━━━━━━━━━━\n"
    text += f"<pre>{chunks[index]}</pre>\n"
    text += f"━━━━━━━━━━━━━━━\n"
    text += f"💡 <i>Keyingi sahifa uchun:</i> <code>.rf {index + 2}</code>"
    
    await event.edit(text, parse_mode='html')
