from telethon import events, functions, types
from database import update_session_setting, get_sessions
import asyncio

async def setup_auto_settings(client, user_id):
    @client.on(events.NewMessage(pattern=r'\.read (on|off)', outgoing=True))
    async def toggle_read(event):
        mode = event.pattern_match.group(1)
        val = 1 if mode == "on" else 0
        update_session_setting(user_id, "read", val)
        await event.edit(f"<b>📑 Avtomatik oʻqish rejimi {'yoqildi' if val else 'oʻchirildi'}!</b>", parse_mode='html')

    @client.on(events.NewMessage(pattern=r'\.typing (on|off)', outgoing=True))
    async def toggle_typing(event):
        mode = event.pattern_match.group(1)
        val = 1 if mode == "on" else 0
        update_session_setting(user_id, "typing", val)
        await event.edit(f"<b>📝 Yozmoqda... rejimi {'yoqildi' if val else 'oʻchirildi'}!</b>", parse_mode='html')

    @client.on(events.NewMessage(pattern=r'\.online (on|off)', outgoing=True))
    async def toggle_online(event):
        mode = event.pattern_match.group(1)
        val = 1 if mode == "on" else 0
        update_session_setting(user_id, "online", val)
        await event.edit(f"<b>🖥 24 soat online rejimi {'yoqildi' if val else 'oʻchirildi'}!</b>", parse_mode='html')

    # Better approach for incoming messages
    @client.on(events.NewMessage())
    async def global_handler(event):
        try:
            sessions = get_sessions()
            curr = next((s for s in sessions if str(s["user_id"]) == str(user_id)), None)
            if not curr: return

            if curr.get("read") == 1 and not event.out:
                await client.send_read_acknowledge(event.chat_id, event.message)
            
            if curr.get("typing") == 1 and not event.out:
                async with client.action(event.chat_id, 'typing'):
                    await asyncio.sleep(2)
        except Exception:
            pass
