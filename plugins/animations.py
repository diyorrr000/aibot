from telethon import events, types
import asyncio

async def run_animation(event, frames, delay=0.3, custom_emoji_id=None):
    for frame in frames:
        try:
            if custom_emoji_id:
                # Custom Emoji uchun maxsus entity yaratamiz
                await event.edit(frame, entities=[types.MessageEntityCustomEmoji(offset=0, length=len(frame), document_id=int(custom_emoji_id))])
            else:
                await event.edit(frame)
            await asyncio.sleep(delay)
        except Exception:
            break

async def setup_animations(client):
    # Foydalanuvchi taqdim etgan Premium ID
    HEART_ID = 5352729084289883641

    @client.on(events.NewMessage(pattern=r'\.snow', outgoing=True))
    async def snow_anim(event):
        frames = [
            "☀️", "   ☀️\n☁️", "     ☀️\n☁️ ☁️", "☁️ ☁️ ☁️", "☁️ ☁️ ☁️  ☁️",
            "☁️ ☁️ ☁️  ☁️ ☁️", "☁️ ☁️ ☁️  ☁️ ☁️ ☁️", "☁️ ☁️ ☁️  ☁️ ☁️ ☁️\n           💧💧💧",
            "☁️☁️☁️☁️☁️☁️☁️", "           ❄️\n     💧    💧💧💧💧\n\n💧 💧 💧 💧 💧 💧"
        ]
        await run_animation(event, frames)

    @client.on(events.NewMessage(pattern=r'\.xd', outgoing=True))
    async def xd_anim(event):
        frames = ["🤣", "🤣🤣", "🤣🤣🤣", "🤣🤣🤣🤣", "🤣🤣🤣🤣🤣", "🤣🤣🤣🤣🤣🤣", "🤣🤣🤣🤣🤣🤣🤣"]
        await run_animation(event, frames)

    @client.on(events.NewMessage(pattern=r'\.lovee', outgoing=True))
    async def lovee_anim(event):
        frames = ['🚶‍♀________________🏃‍♂', '🚶‍♀_______________🏃‍♂', '🚶‍♀__🏃‍♂', '🚶‍♀_🏃‍♂', '💙love💙']
        await run_animation(event, frames, delay=0.1)

    @client.on(events.NewMessage(pattern=r'\.fuck', outgoing=True))
    async def fuck_anim(event):
        frames = [
            "              \\             \\ ' ",
            "            \\              (\n              \\             \\ ' ",
            "        ('(   (   (   (  ¯~/'  ' /\n         \\                         /\n          \\                _.•´\n            \\              (\n              \\             \\ ' ",
            " .                        /¯)\n                         /   /\n                      /    /\n              /´¯/'   '/´¯¯•¸\n           /'/   /    /  /     /¨¯\\\n         ('(   (   (   (  ¯~/'  ' /\n          \\                         /\n           \\                _.•´\n             \\              (\n               \\             \\ ' "
        ]
        await run_animation(event, frames, delay=0.3)

    @client.on(events.NewMessage(pattern=r'\.police', outgoing=True))
    async def police_anim(event):
        frames = ['🟦🟦🟦🔴🔴🔴🟦🟦🟦', '🟥🟥🟥🔵🔵🔵🟥🟥🟥'] * 5
        await run_animation(event, frames, delay=0.3)

    @client.on(events.NewMessage(pattern=r'\.kill', outgoing=True))
    async def kill_anim(event):
        frames = ["😂                 • 🔫🤠", "😂•                  🔫🤠", "🤯                  🔫 🤠", "🤠"]
        await run_animation(event, frames, delay=0.3)

    @client.on(events.NewMessage(pattern=r'\.ari', outgoing=True))
    async def ari_anim(event):
        frames = ['🏥__________🏃‍♂️______________🐝', '🏥___🏃‍♂️___🐝', '🏥_🏃‍♂️_🐝', 'Tugadi..☹️🐝']
        await run_animation(event, frames, delay=0.3)

    @client.on(events.NewMessage(pattern=r'\.load', outgoing=True))
    async def load_anim(event):
        frames = ["▪️10%", "▪️▪️30%", "▪️▪️▪️50%", "▪️▪️▪️▪️70%", "▪️▪️▪️▪️▪️90%", "❗️ERROR❗️"]
        await run_animation(event, frames, delay=0.3)

    @client.on(events.NewMessage(pattern=r'\.god', outgoing=True))
    async def god_anim(event):
        frames = ["🕌                  🚶‍♂", "🕌        🚶‍♂", "🕌🚶‍♂", "اشه Ey Ollohni Unutmaylik !"]
        await run_animation(event, frames, delay=0.3)

    @client.on(events.NewMessage(pattern=r'\.snake', outgoing=True))
    async def snake_anim(event):
        frames = ["🐍                         🦅", "🐍            🦅", "🐍🦅", "😹"]
        await run_animation(event, frames, delay=0.3)

    @client.on(events.NewMessage(pattern=r'\.ghost', outgoing=True))
    async def ghost_anim(event):
        frames = ["👻                                   🙀", "👻                  🙀", "👻🙀", "☠Kill☠"]
        await run_animation(event, frames, delay=0.1)

    @client.on(events.NewMessage(pattern=r'\.cosmo', outgoing=True))
    async def cosmo_anim(event):
        frames = ["🌍🚀                                🛸", "🌍🚀            🛸", "🌍🚀🛸", "🌍💥Boom💥"]
        await run_animation(event, frames, delay=0.1)

    @client.on(events.NewMessage(pattern=r'\.dance', outgoing=True))
    async def dance_anim(event):
        frames = ["🏡 💃", "🏡      💃", "🏡              ��💔👫", "🏡🚶‍♀"]
        await run_animation(event, frames, delay=0.2)

    @client.on(events.NewMessage(pattern=r'\.yurak', outgoing=True))
    async def yurak_anim(event):
        colors = ["❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "💗"]
        frames = []
        for c in colors:
            frames.append(f'.           {c}                  {c}\n        {c}  {c}          {c}  {c}\n    {c}          {c}  {c}          {c}\n       {c}           {c}           {c}\n           {c}                    {c}\n               {c}            {c}\n                   {c}    {c}\n                        {c}\n.')
        await run_animation(event, frames, delay=0.5)

    @client.on(events.NewMessage(pattern=r'\.love', outgoing=True))
    async def love_anim(event):
        frames = ["🤍", "🤍🤍", "🤍🤍🤍", "🤍🤍🤍🤍", "🤍🤍🤍🤍🤍", "🤍🤍🤍🤍🤍🤍", "🤍🤍🤍🤍🤍🤍🤍", "🤍🤍🤍🤍🤍🤍🤍🤍", "🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍❤️❤️🤍❤️❤️🤍🤍", "🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍❤️❤️🤍❤️❤️🤍🤍\n🤍❤️❤️❤️❤️❤️❤️❤️🤍", "<b>I ❤️ MOM!</b>"]
        await run_animation(event, frames, delay=0.3)

    @client.on(events.NewMessage(pattern=r'\.dengiz', outgoing=True))
    async def dengiz_anim(event):
        frames = ["🏝┄┅┄┅┄┄┅🏊‍♂┅┄┄┅🦈", "🏝┄┅┄🏊‍♂┅┄🦈", "🏝🏊‍♂┅┄🦈", "🦈"]
        await run_animation(event, frames, delay=0.3)

    @client.on(events.NewMessage(pattern=r'\.knife', outgoing=True))
    async def knife_anim(event):
        frames = ["🔪                🎈", "🔪          🎈", "🔪🎈", "💥Boom💥"]
        await run_animation(event, frames, delay=0.2)

    @client.on(events.NewMessage(pattern=r'\.chaqmoq', outgoing=True))
    async def chaqmoq_anim(event):
        frames = ["☁️                ⚡️", "☁️         ⚡️", "☁️ ⚡️", "⛈"]
        await run_animation(event, frames, delay=0.3)

    @client.on(events.NewMessage(pattern=r'\.home', outgoing=True))
    async def home_anim(event):
        frames = ["🏠              🚶‍♂", "🏠        🚶‍♂", "🏠🚶‍♂"]
        await run_animation(event, frames, delay=0.2)

    @client.on(events.NewMessage(pattern=r'\.ayriliq', outgoing=True))
    async def ayriliq_anim(event):
        frames = ["❤️🧡💛💚", "💜💙🖤💛", "🤍🤎💛💜", "💚❤️🖤🧡", "💜💚🧡🖤"]
        await run_animation(event, frames, delay=0.4)

    @client.on(events.NewMessage(pattern=r'\.puq', outgoing=True))
    async def puq_anim(event):
        frames = ["💩               🤢", "💩     🤢", "💩 🤢", "🤮🤮"]
        await run_animation(event, frames, delay=0.3)

    @client.on(events.NewMessage(pattern=r'\.money', outgoing=True))
    async def money_anim(event):
        frames = ["🔥                                 💵", "🔥                 💵", "🔥 💵", "💸"]
        await run_animation(event, frames, delay=0.1)

    @client.on(events.NewMessage(pattern=r'\.search', outgoing=True))
    async def search_anim(event):
        frames = ["👽                     🔦😼", "👽          🔦😼", "👽🔦🙀"]
        await run_animation(event, frames, delay=0.1)
