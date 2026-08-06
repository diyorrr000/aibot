import time
import os
import psutil
from telethon import events
from config import ADMIN_ID

async def setup_commands(client):
    @client.on(events.NewMessage(pattern=r'\.help', outgoing=True))
    async def help_cmd(event):
        help_text = """✅ <b>User bot buyruqlari:

.help - 🖥 User botdan foydalanish boʻyicha qoʻllanma!
.ping - 🚀 User bot tezligini tekshirish!
.restart - 🔄 User botni qayta ishga tushirish!
.status - 💾 Server holati!
.read on/off - 📑 Avtomatik oʻqish!
.typing on/off - 📝 Yozmoqda...!
.online on/off - 🖥 24 soat online!
.soat on/off - 🕒 Ismga soat!
.soatbio on/off - 🕒 Bioga soat!
.func - 🎭 Animatsiyalar ro'yxati!</b>"""
        await event.edit(help_text, parse_mode='html')

    @client.on(events.NewMessage(pattern=r'\.func', outgoing=True))
    @client.on(events.NewMessage(pattern=r'\.komandalar', outgoing=True))
    @client.on(events.NewMessage(pattern=r'\.co', outgoing=True))
    async def func_cmd(event):
        func_text = """✅ <b>🎭 Animatsiyalar:</b>
<code>.love</code>, <code>.yurak</code>, <code>.police</code>, <code>.fuck</code>, <code>.kill</code>, <code>.ari</code>, <code>.load</code>, <code>.god</code>, <code>.snake</code>, <code>.ghost</code>, <code>.cosmo</code>, <code>.dance</code>, <code>.knife</code>, <code>.chaqmoq</code>, <code>.home</code>, <code>.ayriliq</code>, <code>.money</code>, <code>.search</code>, <code>.snow</code>, <code>.xd</code>

🌀 <b>RolePlay (.me, .do, .try, .todo):</b>
<code>.me</code> - Birinchi shaxs nomidan
<code>.do</code> - Atrofdagi voqea
<code>.try</code> - Omadingizni sinash
<code>.todo</code> - Fraza va harakat

📂 <b>Qo'shimcha modullar:</b>
<code>.acc</code> - Akkunt haqida ma'lumot
<code>.ai</code> - Sun'iy intellekt (reply)
<code>.baza</code> - Guruh a'zolarini yig'ish
<code>.st</code> - Kanalga auto-reaksiya
<code>.r</code> - Stiker yasash (reply)
<code>.rf</code> - Faylni o'qish (reply)
<code>.x</code> - Cheklangan postni ko'chirish
<code>.gender</code> - Jinsni aniqlash
<code>.ro</code> - Rus ruletkasi
<code>.shlink</code> - Linkni qisqartirish
<code>.yt</code> - YouTube dan qidirish
<code>.t2s</code> - Matnni ovoz qilish
<code>.atts</code> - O'yinlar ovozi (Dota, WoW)
<code>.tr</code> - Tarjimon (Google)
<code>.kurs</code> - Valyuta kurslari (MB)
<code>.q</code> - Xabarni stiker qilish (reply)
<code>.auto</code> - Auto-reklama yoqish
<code>.telegraph</code> - Telegraph maqola yaratish
<code>.rmeme</code> - Tasodifiy memlar
<code>.catbox</code>, <code>.envs</code>, <code>.kappa</code> - Fayl yuklash
<code>.voice</code>, <code>.music</code> - Musiqa qidirish
<code>.weather</code> - Havoni tekshirish
<code>.lyrics</code> - Qo'shiq matni qidirish
<code>.soat</code>, <code>.soatbio</code> - Profil soati
<code>.time</code>, <code>.settime</code> - Timer (Voqegacha vaqt)

<b>AnimeTools (.fa, .aq, .ra):</b>
<code>.fa</code> - Animeni rasm orqali qidirish
<code>.aq</code> - Anime sitatalari
<code>.ra</code> - Tasodifiy anime tavsiyasi

<b>AnimeArts (.art, .nsfwart):</b>
<code>.art</code> - Yoqimli anime surat (SFW)
<code>.nsfwart</code> - Anime surat (NSFW)

<code>.getid</code> - Premium emoji ID olish</b>"""
        await event.edit(func_text, parse_mode='html')

    @client.on(events.NewMessage(pattern=r'\.ping', outgoing=True))
    async def ping_cmd(event):
        start = time.time()
        await event.edit("✅ <b>Ping: Tekshirilmoqda...</b>", parse_mode='html')
        end = time.time()
        ms = round((end - start) * 1000)
        await event.edit(f"✅ <b>Ping: {ms} ms</b>", parse_mode='html')

    @client.on(events.NewMessage(pattern=r'\.voice (.*)', outgoing=True))
    async def voice_cmd(event):
        query = event.pattern_match.group(1)
        await event.edit(f"✅ <b>( `{query}` ) nomli ovozli xabar qidirilmoqda...</b>", parse_mode='html')
        results = await client.inline_query("@ovozqanibot", query)
        if results:
            await results[0].click(event.chat_id, reply_to=event.reply_to_msg_id or event.id)
            await event.delete()

    @client.on(events.NewMessage(pattern=r'\.music (.*)', outgoing=True))
    async def music_cmd(event):
        query = event.pattern_match.group(1)
        await event.edit(f"✅ <b>( `{query}` ) nomli musiqa qidirilmoqda...</b>", parse_mode='html')
        results = await client.inline_query("@anymelody_bot", query)
        if results:
            await results[0].click(event.chat_id, reply_to=event.reply_to_msg_id or event.id)
            await event.delete()


    @client.on(events.NewMessage(pattern=r'\.status', outgoing=True))
    async def status_cmd(event):
        process = psutil.Process(os.getpid())
        mem = process.memory_info().rss / (1024 * 1024)
        await event.edit(f"✅ <b>Xotiradan foydalanish: {mem:.2f} Mb</b>", parse_mode='html')

    @client.on(events.NewMessage(pattern=r'\.getid', outgoing=True))
    async def get_emoji_id(event):
        reply = await event.get_reply_message()
        msg = reply if reply else event.message
        
        if msg.entities:
            for ent in msg.entities:
                if isinstance(ent, types.MessageEntityCustomEmoji):
                    await event.edit(f"✅ <b>Premium Emoji ID:</b> <code>{ent.document_id}</code>", parse_mode='html')
                    return
        
        await event.edit("❌ <b>Bu xabarda premium emoji topilmadi!</b>")
