from telethon import events, functions
import asyncio
from datetime import datetime
import os
import pytz

CHECK_EMOJI = "✅"
CLOCK_EMOJI = "🕒"

# O'zbekiston vaqti
UZB_TZ = pytz.timezone('Asia/Tashkent')

# Tasklarni saqlash uchun lug'at: {user_id: {"name": task, "bio": task}}
CLOCK_TASKS = {}
# Original ma'lumotlarni saqlash: {user_id: {"name": "Ism", "bio": "Bio"}}
ORIGINAL_DATA = {}

async def setup_clock(client):
    me = await client.get_me()
    user_id = me.id
    
    if user_id not in CLOCK_TASKS:
        CLOCK_TASKS[user_id] = {"name": None, "bio": None}
    
    if user_id not in ORIGINAL_DATA:
        full = await client(functions.users.GetFullUserRequest(id='me'))
        ORIGINAL_DATA[user_id] = {
            "first_name": me.first_name,
            "last_name": me.last_name or "",
            "about": full.full_user.about or ""
        }

    @client.on(events.NewMessage(pattern=r'\.soat(?: (on|off))?', outgoing=True))
    async def clock_name_handler(event):
        mode = event.pattern_match.group(1)
        if not mode:
            await event.edit("<b>Xato ishlatish!</b>\n\n<blockquote>Namuna: <code>.soat on</code> yoki <code>.soat off</code></blockquote>", parse_mode='html')
            return
        
        if mode == "on":
            if CLOCK_TASKS[user_id]["name"]:
                await event.edit("<b>Ismdagi soat allaqachon yoqilgan!</b>")
                return
            
            curr_me = await client.get_me()
            ORIGINAL_DATA[user_id]["first_name"] = curr_me.first_name
            ORIGINAL_DATA[user_id]["last_name"] = curr_me.last_name or ""

            async def name_loop():
                while True:
                    try:
                        now = datetime.now(UZB_TZ).strftime("%H:%M")
                        new_first_name = f"{ORIGINAL_DATA[user_id]['first_name']}"
                        new_last_name = f"{ORIGINAL_DATA[user_id]['last_name']} | {now}".strip()
                        if new_last_name.startswith("|"):
                             new_last_name = f"| {now}"
                        
                        await client(functions.account.UpdateProfileRequest(
                            first_name=new_first_name,
                            last_name=new_last_name
                        ))
                    except Exception:
                        pass
                    await asyncio.sleep(60)

            CLOCK_TASKS[user_id]["name"] = asyncio.create_task(name_loop())
            await event.edit(f"{CHECK_EMOJI} <b>Ismdagi soat yoqildi!</b>")
            
        else:
            if CLOCK_TASKS[user_id]["name"]:
                CLOCK_TASKS[user_id]["name"].cancel()
                CLOCK_TASKS[user_id]["name"] = None
                await client(functions.account.UpdateProfileRequest(
                    first_name=ORIGINAL_DATA[user_id]["first_name"],
                    last_name=ORIGINAL_DATA[user_id]["last_name"]
                ))
                await event.edit(f"{CHECK_EMOJI} <b>Ismdagi soat o'chirildi va ism qaytarildi.</b>")
            else:
                await event.edit("<b>Ismdagi soat yoqilmagan edi.</b>")

    @client.on(events.NewMessage(pattern=r'\.soatbio(?: (on|off))?', outgoing=True))
    async def clock_bio_handler(event):
        mode = event.pattern_match.group(1)
        if not mode:
            await event.edit("<b>Xato ishlatish!</b>\n\n<blockquote>Namuna: <code>.soatbio on</code> yoki <code>.soatbio off</code></blockquote>", parse_mode='html')
            return
        
        if mode == "on":
            if CLOCK_TASKS[user_id]["bio"]:
                await event.edit("<b>Biodagi soat allaqachon yoqilgan!</b>")
                return
            
            full = await client(functions.users.GetFullUserRequest(id='me'))
            ORIGINAL_DATA[user_id]["about"] = full.full_user.about or ""

            async def bio_loop():
                while True:
                    try:
                        now_time = datetime.now(UZB_TZ).strftime("%H:%M")
                        now_date = datetime.now(UZB_TZ).strftime("%d.%m.%Y")
                        new_bio = f"🕒 Soat: {now_time} | 📅 Sana: {now_date}"
                        
                        await client(functions.account.UpdateProfileRequest(
                            about=new_bio
                        ))
                    except Exception:
                        pass
                    await asyncio.sleep(60)

            CLOCK_TASKS[user_id]["bio"] = asyncio.create_task(bio_loop())
            await event.edit(f"{CHECK_EMOJI} <b>Biodagi soat yoqildi!</b>")
            
        else:
            if CLOCK_TASKS[user_id]["bio"]:
                CLOCK_TASKS[user_id]["bio"].cancel()
                CLOCK_TASKS[user_id]["bio"] = None
                await client(functions.account.UpdateProfileRequest(
                    about=ORIGINAL_DATA[user_id]["about"]
                ))
                await event.edit(f"{CHECK_EMOJI} <b>Biodagi soat o'chirildi va bio qaytarildi.</b>")
            else:
                await event.edit("<b>Biodagi soat yoqilmagan edi.</b>")
