from telethon import events, functions, types
import os

async def setup_baza(client):
    @client.on(events.NewMessage(pattern=r'\.baza(?: (.*))?', outgoing=True))
    async def baza_handler(event):
        target = event.pattern_match.group(1)
        
        if not target:
            if event.is_private:
                await event.edit("🚫 <b>Iltimos, guruh username yozing yoki guruh ichida ishlating!</b>", parse_mode='html')
                return
            chat = await event.get_chat()
        else:
            try:
                chat = await client.get_entity(target)
            except Exception as e:
                await event.edit(f"🚫 <b>Xato: {e}</b>", parse_mode='html')
                return

        await event.edit("✅ <b>Foydalanuvchilar yig'ilmoqda...</b>", parse_mode='html')
        
        try:
            members = await client.get_participants(chat)
            file_name = f"baza_{chat.id}.txt"
            
            with open(file_name, "w", encoding="utf-8") as f:
                for member in members:
                    uid = member.id
                    username = f"@{member.username}" if member.username else "None"
                    name = f"{member.first_name or ''} {member.last_name or ''}".strip() or "None"
                    phone = f"+{member.phone}" if getattr(member, 'phone', None) else "None"
                    
                    f.write(f"ID: {uid} | User: {username} | Name: {name} | Phone: {phone}\n")
            
            # Agar target ko'rsatilgan bo'lsa chatga, bo'lmasa saqlangan xabarlarga
            dest = "me" if not target else event.chat_id
            caption = f"✅ <b>{chat.title} bazasi\n👥 Soni: {len(members)}</b>"
            
            await client.send_file(dest, file_name, caption=caption, parse_mode='html')
            os.remove(file_name)
            await event.delete()
            
        except Exception as e:
            await event.edit(f"🚫 <b>Bazani yig'ishda xato: {e}</b>", parse_mode='html')
