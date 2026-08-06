from telethon import events
import random

CHECK_EMOJI = "✅"
RP_EMOJI = "🌀"

async def setup_roleplay(client):
    @client.on(events.NewMessage(pattern=r'\.me(?: (.*))?', outgoing=True))
    async def me_handler(event):
        """Harakatni birinchi shaxs nomidan yozish"""
        args = event.pattern_match.group(1)
        if not args:
            await event.edit("<b>Harakatni yozing!</b>\n\n<blockquote>Namuna: <code>.me choy ichdi</code></blockquote>", parse_mode='html')
            return
        
        me = await client.get_me()
        nickname = f"{me.first_name} {me.last_name or ''}".strip()
        
        await event.edit(f"{RP_EMOJI} <b>{nickname}</b> <i>{args}</i>", parse_mode='html')

    @client.on(events.NewMessage(pattern=r'\.do(?: (.*))?', outgoing=True))
    async def do_handler(event):
        """Atrofdagi voqeani tasvirlash"""
        args = event.pattern_match.group(1)
        if not args:
            await event.edit("<b>Voqeani yozing!</b>\n\n<blockquote>Namuna: <code>.do Quyosh chiqdi</code></blockquote>", parse_mode='html')
            return
            
        me = await client.get_me()
        nickname = f"{me.first_name} {me.last_name or ''}".strip()
        
        await event.edit(f"{RP_EMOJI} <i>{args}</i> - | <b>{nickname}</b>", parse_mode='html')

    @client.on(events.NewMessage(pattern=r'\.try(?: (.*))?', outgoing=True))
    async def try_handler(event):
        """Harakat omadini tekshirish"""
        args = event.pattern_match.group(1)
        if not args:
            await event.edit("<b>Harakatni yozing!</b>\n\n<blockquote>Namuna: <code>.try moshina o't oldi</code></blockquote>", parse_mode='html')
            return
            
        me = await client.get_me()
        nickname = f"{me.first_name} {me.last_name or ''}".strip()
        
        result = random.choice([
            "<b>✅ Muvaffaqiyatli</b>", 
            "<b>❌ Muvaffaqiyatsiz</b>"
        ])
        
        await event.edit(f"{RP_EMOJI} <b>{nickname}</b> <i>{args}</i> - | {result}", parse_mode='html')

    @client.on(events.NewMessage(pattern=r'\.todo(?: (.*))?', outgoing=True))
    async def todo_handler(event):
        """Fraza va harakatni birlashtirish"""
        args_raw = event.pattern_match.group(1)
        if not args_raw or " " not in args_raw.strip():
             await event.edit("<b>Xato format!</b>\n\n<blockquote>Namuna: <code>.todo Salom. qo'l silkitib</code></blockquote>", parse_mode='html')
             return
             
        parts = args_raw.strip().split(maxsplit=1)
        phrase, action = parts[0], parts[1]
        
        me = await client.get_me()
        nickname = f"{me.first_name} {me.last_name or ''}".strip()
        
        await event.edit(f"{RP_EMOJI} <i>'{phrase}', - dedi </i><b>{nickname}</b>, <i>{action}.</i>", parse_mode='html')
