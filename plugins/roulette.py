from telethon import events, functions
import random
import asyncio
import os

CHECK_EMOJI = "✅"
ERROR_EMOJI = "🚫 "

async def setup_roulette(client):
    @client.on(events.NewMessage(pattern=r'\.ro', outgoing=True))
    async def roulette_handler(event):
        """Rus ruletkasi o'yini"""
        # O'yin holati
        bullet = random.randint(1, 5)
        current = random.randint(1, 5)
        
        await event.edit(f"🔫 <b>To'pponchani o'qladingiz...</b>\n\n🔗 <b>O'q:</b> {current}/5\n\n👁️🗨️ <b>Hozir otamiz...</b>", parse_mode='html')
        await asyncio.sleep(2)
        
        if bullet == current:
            # Yutqazdi
            punishments = [
                "Ismni g'alati ismga o'zgartirish",
                "Botni qayta ishga tushirish",
                "Guruhdagilarni 'bezovta' qilish (tag)",
                "Hech narsa bo'lmadi, omadingiz bor ekan!"
            ]
            punishment = random.choice(punishments)
            
            await event.edit(f"🫨 <b>PAX! O'q tegdi.</b>\n\n😵💫 <b>Jazo:</b> <code>{punishment}</code>", parse_mode='html')
            
            # Jazolarni ijro etish
            if punishment == "Ismni g'alati ismga o'zgartirish":
                names = ["Doxer", "Pubertat", "Venom", "Hacked", "Sariq Bola", "Bot Voy"]
                new_name = random.choice(names)
                try:
                    await client(functions.account.UpdateProfileRequest(first_name=new_name))
                except: pass
                
            elif punishment == "Botni qayta ishga tushirish":
                await event.respond(f"{CHECK_EMOJI} <b>Bot jazo tariqasida qayta ishga tushmoqda...</b>")
                await asyncio.sleep(1)
                os._exit(0) # Qayta ishga tushirish Render/Local managerga bog'liq
                
            elif punishment == "Guruhdagilarni 'bezovta' qilish (tag)":
                if event.is_group:
                    try:
                        participants = await client.get_participants(event.chat_id, limit=5)
                        tags = " ".join([f"@{u.username}" for u in participants if u.username])
                        if tags:
                            await event.respond(f"🏷 <b>Jazo - hamma ko'rsin:</b> {tags}")
                    except: pass
        else:
            # Omad keldi
            new_bullet = random.randint(1, 5)
            await event.edit(f"🙂 <b>Omadingiz keldi! O'q tegmasdan o'tib ketdi.</b>\n\n🔗 <b>Xavfli o'q:</b> {bullet}\n👁️🗨️ <b>Keyingi safar ehtiyot bo'ling!</b>", parse_mode='html')
