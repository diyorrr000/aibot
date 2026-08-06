from telethon import events, functions, types
import asyncio

# Kanal va reaksiyalar uchun vaqtinchalik xotira
TARGET_CHANNELS = {} # {peer_id: [reactions]}

async def setup_reactions(client):
    @client.on(events.NewMessage(pattern=r'\.st (.*)', outgoing=True))
    async def st_handler(event):
        target = event.pattern_match.group(1)
        try:
            channel = await client.get_entity(target)
            
            # Kanalning mavjud reaksiyalarini olish
            full_chat = await client(functions.channels.GetFullChannelRequest(channel))
            available = []
            if full_chat.full_chat.available_reactions:
                # Telethon version dependent, but usually it's a list of reaction types
                # Simple fallback to a few defaults if we can't parse perfectly
                available = ["👍", "🔥", "❤️", "🤩", "👏"] # Default logic
            
            TARGET_CHANNELS[channel.id] = available
            
            await event.edit(f"✅ <b>{target} kuzatuvga olindi. Postlarga reaksiya bosiladi!</b>", parse_mode='html')
            
            # Oldingi 5ta postga reaksiya bosish
            messages = await client.get_messages(channel, limit=5)
            for msg in messages:
                try:
                    await client(functions.messages.SendReactionRequest(
                        peer=channel,
                        msg_id=msg.id,
                        reaction=[types.ReactionEmoji(emojis[0])] if (emojis := TARGET_CHANNELS.get(channel.id)) else [types.ReactionEmoji("👍")]
                    ))
                    await asyncio.sleep(1)
                except:
                    pass
                    
        except Exception as e:
            await event.edit(f"🚫 <b>Xato: {e}</b>", parse_mode='html')

    @client.on(events.NewMessage())
    async def reaction_watcher(event):
        if event.chat_id in TARGET_CHANNELS:
            try:
                emojis = TARGET_CHANNELS[event.chat_id]
                await client(functions.messages.SendReactionRequest(
                    peer=event.chat_id,
                    msg_id=event.id,
                    reaction=[types.ReactionEmoji(emojis[0])] if emojis else [types.ReactionEmoji("👍")]
                ))
            except:
                pass
