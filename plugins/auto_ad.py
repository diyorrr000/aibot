from telethon import events, functions
import asyncio
import time

CHECK_EMOJI = "✅"
ERROR_EMOJI = "❌"

# Reklama vazifalarini saqlash: {chat_id: task}
AUTO_TASKS = {}

async def setup_auto_ad(client):
    @client.on(events.NewMessage(pattern=r'\.auto (.*)', outgoing=True))
    async def auto_ad_handler(event):
        """Avtomatik reklama yuborishni boshlash"""
        input_str = event.pattern_match.group(1)
        
        # Format: link vaqt | xabar
        try:
            if "|" not in input_str:
                raise ValueError
            
            part1, message = input_str.split("|", 1)
            part1_parts = part1.strip().split()
            
            if len(part1_parts) < 2:
                raise ValueError
                
            link = part1_parts[0]
            interval = int(part1_parts[1])
            message = message.strip()
            
            if interval < 10:
                await event.edit(f"{ERROR_EMOJI} <b>Vaqt kamida 10 soniya bo'lishi kerak!</b>")
                return

            # Guruhni olish
            try:
                entity = await client.get_entity(link)
                chat_id = entity.id
            except Exception:
                await event.edit(f"{ERROR_EMOJI} <b>Guruh linki noto'g'ri yoki bot guruhga a'zo emas!</b>")
                return

            # Agar eski task bo'lsa to'xtatish
            if chat_id in AUTO_TASKS:
                AUTO_TASKS[chat_id].cancel()

            async def ad_loop():
                while True:
                    try:
                        await client.send_message(chat_id, message)
                    except Exception:
                        pass
                    await asyncio.sleep(interval)

            task = asyncio.create_task(ad_loop())
            AUTO_TASKS[chat_id] = task
            
            await event.edit(
                f"{CHECK_EMOJI} <b>Auto-reklama yoqildi!</b>\n\n"
                f"👥 <b>Guruh:</b> <code>{link}</code>\n"
                f"⏳ <b>Interval:</b> <code>{interval}</code> soniya\n"
                f"📝 <b>Xabar:</b> <i>{message[:50]}...</i>\n\n"
                f"To'xtatish uchun: <code>.stopauto {link}</code>",
                parse_mode='html'
            )

        except (ValueError, IndexError):
            await event.edit(
                f"{ERROR_EMOJI} <b>Xato ishlatish!</b>\n\n"
                f"📝 <b>Namuna:</b>\n"
                f"<code>.auto @guruhlink 60 | Sotiladi iPhone 15!</code>\n\n"
                f"☝️ <i>Eslatma: Link va vaqtdan keyin '|' belgisini qo'ying!</i>",
                parse_mode='html'
            )

    @client.on(events.NewMessage(pattern=r'\.stopauto (.*)', outgoing=True))
    async def stop_auto_handler(event):
        link = event.pattern_match.group(1).strip()
        try:
            entity = await client.get_entity(link)
            chat_id = entity.id
            if chat_id in AUTO_TASKS:
                AUTO_TASKS[chat_id].cancel()
                del AUTO_TASKS[chat_id]
                await event.edit(f"{CHECK_EMOJI} <b>{link} uchun auto-reklama to'xtatildi!</b>")
            else:
                await event.edit(f"{ERROR_EMOJI} <b>Bu guruhda faol reklama topilmadi.</b>")
        except Exception:
            await event.edit(f"{ERROR_EMOJI} <b>Xato! Linkni to'g'ri yozing.</b>")
