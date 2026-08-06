from telethon import events
import random
import asyncio

CHECK_EMOJI = "✅"
ERROR_EMOJI = "🚫"

async def setup_random_memes(client):
    async def get_random_meme(channel):
        try:
            chat = await client.get_entity(channel)
            messages = await client.get_messages(chat, limit=300)
            media_messages = [msg for msg in messages if msg.media]
            
            if not media_messages:
                return None
                
            return random.choice(media_messages)
        except Exception:
            return None

    @client.on(events.NewMessage(pattern=r'\.rmeme', outgoing=True))
    async def rmeme_handler(event):
        """Tasodifiy kulgili memlarni yuborish (Safe)"""
        await event.edit(f"{CHECK_EMOJI} <b>Tasodifiy mem qidirilmoqda...</b>", parse_mode='html')
        
        random_msg = await get_random_meme("prikoly_i_memy")
        
        if not random_msg:
            await event.edit(f"{ERROR_EMOJI} <b>Mem topishda xatolik yuz berdi!</b>", parse_mode='html')
            return
        
        await client.send_file(
            event.chat_id,
            random_msg.media,
            caption=f"{CHECK_EMOJI} <b>Marhamat, tasodifiy mem!</b>",
            parse_mode='html',
            reply_to=event.reply_to_msg_id
        )
        await event.delete()

    @client.on(events.NewMessage(pattern=r'\.rnmeme', outgoing=True))
    async def rnmeme_handler(event):
        """Tasodifiy NSFW/Kattalar uchun memlarni yuborish"""
        await event.edit(f"{CHECK_EMOJI} <b>Tasodifiy mem qidirilmoqda...</b>", parse_mode='html')
        
        random_msg = await get_random_meme("po_memes")
        
        if not random_msg:
            await event.edit(f"{ERROR_EMOJI} <b>Mem topishda xatolik yuz berdi!</b>", parse_mode='html')
            return
        
        await client.send_file(
            event.chat_id,
            random_msg.media,
            caption=f"{CHECK_EMOJI} <b>Marhamat, maxsus mem!</b>",
            parse_mode='html',
            reply_to=event.reply_to_msg_id
        )
        await event.delete()
