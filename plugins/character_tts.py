from telethon import events
import asyncio

CHECK_EMOJI = "✅"

async def setup_character_tts(client):
    @client.on(events.NewMessage(pattern=r'\.atts(?: (.*))?', outgoing=True))
    async def atts_handler(event):
        """O'yin qahramonlari ovozi bilan gapirish"""
        args = event.pattern_match.group(1)
        if not args or len(args.split()) < 2:
            await event.edit(
                "<b>Xato ishlatish!</b>\n\n"
                f"📝 <b>Namuna:</b> <code>.atts arthas Salom dunyo</code>\n\n"
                f"Ovozlar ro'yxati uchun: <code>.atts_list</code>",
                parse_mode='html'
            )
            return
        
        parts = args.split(maxsplit=1)
        hero, text = parts[0], parts[1]
        
        await event.edit(f"{CHECK_EMOJI} <b>`{hero}` ovozi tayyorlanmoqda...</b>", parse_mode='html')
        
        reply = await event.get_reply_message()
        bot_username = "@silero_voice_bot"
        
        try:
            async with client.conversation(bot_username, timeout=30) as conv:
                # Botga xabar yuborish
                send_msg = await conv.send_message(f"{hero} {text}")
                
                # Javobni kutish
                try:
                    response = await conv.get_response()
                except asyncio.TimeoutError:
                    await event.edit(f"<b>Bot javob bermadi. Iltimos, {bot_username} botiga o'tib, /start bosing!</b>")
                    return

                if not response.media:
                    await event.edit(f"<b>Ovoz chiqarib bo'lmadi. {bot_username} botiga o'tib, sozlab ko'ring.</b>")
                    return
                
                # Ovozli xabarni yuborish
                await client.send_file(
                    event.chat_id,
                    response.media,
                    voice_note=True,
                    reply_to=reply.id if reply else None
                )
                await event.delete()
                
        except Exception as e:
            await event.edit(f"<b>Xatolik yuz berdi:</b> <code>{str(e)}</code>")

    @client.on(events.NewMessage(pattern=r'\.atts_list', outgoing=True))
    @client.on(events.NewMessage(pattern=r'\.warcraftv', outgoing=True))
    async def warcraftv_handler(event):
        await event.edit(
            "💬 <b>Warcraft III Voices:</b>\n\n"
            "<code>arthas</code> | <code>kelthuzad</code> | <code>anubarak</code> | <code>thrall</code> | "
            "<code>grunt</code> | <code>cairne</code> | <code>rexxar</code> | <code>uther</code> | "
            "<code>jaina</code> | <code>kael</code> | <code>garithos</code> | <code>malev</code> | "
            "<code>naisha</code> | <code>tyrande</code> | <code>furion</code> | <code>illidan</code> | "
            "<code>ladyvashj</code> | <code>narrator</code> | <code>medivh</code> | <code>villagerm</code> | "
            "<code>acolyte</code> | <code>sylvanas</code> | <code>dread_bm</code> | <code>dread_t</code> | "
            "<code>illidan_f</code> | <code>mannoroth</code> | <code>muradin</code> | <code>peasant</code> | "
            "<code>priest</code> | <code>sorceress</code> | <code>peon</code> | <code>chen</code>",
            parse_mode='html'
        )

    @client.on(events.NewMessage(pattern=r'\.silerov', outgoing=True))
    async def silerov_handler(event):
        await event.edit(
            "👾 <b>Silero Voices:</b>\n\n"
            "<code>aidar</code> | <code>baya</code> | <code>kseniya</code> | <code>xenia</code> | <code>eugene</code>",
            parse_mode='html'
        )

    @client.on(events.NewMessage(pattern=r'\.dotav', outgoing=True))
    async def dotav_handler(event):
        await event.edit(
            "🎮 <b>Dota 2 Voices:</b>\n\n"
            "<code>announcer</code> | <code>antimage</code> | <code>batrider</code> | <code>bloodseeker</code> | "
            "<code>bounty</code> | <code>bristle</code> | <code>clockwerk</code> | <code>doom</code> | "
            "<code>earth</code> | <code>gyro</code> | <code>huskar</code> | <code>juggernaut</code> | "
            "<code>kotl</code> | <code>kunkka</code> | <code>lancer</code> | <code>lina</code> | "
            "<code>luna</code> | <code>meepo</code> | <code>mortred</code> | <code>omni</code> | "
            "<code>pudge</code> | <code>queen</code> | <code>ranger</code> | <code>riki</code> | "
            "<code>shaker</code> | <code>skywrath</code> | <code>sniper</code> | <code>storm</code> | "
            "<code>templar</code> | <code>tide</code> | <code>treant</code> | <code>tusk</code> | "
            "<code>windranger</code> | <code>witchdoctor</code> | <code>wraith</code>",
            parse_mode='html'
        )
    
    # Boshqa listlarni ham kerak bo'lsa bitta qilib chiqarish mumkin yoki alohida
    @client.on(events.NewMessage(pattern=r'\.other_voices', outgoing=True))
    async def other_v_handler(event):
        await event.edit(
            "🔫 <b>Half-Life:</b> <code>alyx, breen, gman, kleiner</code>\n"
            "🔮 <b>Portal 2:</b> <code>glados, wheatley</code>\n"
            "🪅 <b>Starcraft:</b> <code>kerrigan, raynor, tychus</code>\n"
            "⚔️ <b>Skyrim:</b> <code>alduin, lydia, ulfric</code>\n"
            "🛖 <b>Stalker:</b> <code>bandit</code>\n"
            "🏳️🌈 <b>LOL:</b> <code>yuumi, evelynn</code>",
            parse_mode='html'
        )
