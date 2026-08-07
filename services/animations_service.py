import asyncio
from aiogram import Bot

# Animation frames
ANIMATIONS = {
    "snow": [
        "☀️", "   ☀️\n☁️", "     ☀️\n☁️ ☁️", "☁️ ☁️ ☁️", "☁️ ☁️ ☁️  ☁️",
        "☁️ ☁️ ☁️  ☁️ ☁️", "☁️ ☁️ ☁️  ☁️ ☁️ ☁️", "☁️ ☁️ ☁️  ☁️ ☁️ ☁️\n           💧💧💧",
        "☁️☁️☁️☁️☁️☁️☁️", "           ❄️\n     💧    💧💧💧💧\n\n💧 💧 💧 💧 💧 💧"
    ],
    "xd": ["🤣", "🤣🤣", "🤣🤣🤣", "🤣🤣🤣🤣", "🤣🤣🤣🤣🤣", "🤣🤣🤣🤣🤣🤣", "🤣🤣🤣🤣🤣🤣🤣"],
    "love": [
        "🤍", "🤍🤍", "🤍🤍🤍", "🤍🤍🤍🤍", "🤍🤍🤍🤍🤍", "🤍🤍🤍🤍🤍🤍", 
        "🤍🤍🤍🤍🤍🤍🤍", "🤍🤍🤍🤍🤍🤍🤍🤍", "🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍❤️❤️🤍❤️❤️🤍🤍", 
        "🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🤍❤️❤️🤍❤️❤️🤍🤍\n🤍❤️❤️❤️❤️❤️❤️❤️🤍", "<b>I ❤️ MOM!</b>"
    ],
    "police": ['🟦🟦🟦🔴🔴🔴🟦🟦🟦', '🟥🟥🟥🔵🔵🔵🟥🟥🟥'] * 5,
    "kill": ["😂                 • 🔫🤠", "😂•                  🔫🤠", "🤯                  🔫 🤠", "🤠"],
    "ari": ['🏥__________🏃‍♂️______________🐝', '🏥___🏃‍♂️___🐝', '🏥_🏃‍♂️_🐝', 'Tugadi..☹️🐝'],
    "load": ["▪️10%", "▪️▪️30%", "▪️▪️▪️50%", "▪️▪️▪️▪️70%", "▪️▪️▪️▪️▪️90%", "❗️ERROR❗️"],
    "god": ["🕌                  🚶‍♂", "🕌        🚶‍♂", "🕌🚶‍♂", "اشه Ey Ollohni Unutmaylik !"],
    "snake": ["🐍                         🦅", "🐍            🦅", "🐍🦅", "😹"],
    "ghost": ["👻                                   🙀", "👻                  🙀", "👻🙀", "☠Kill☠"],
    "cosmo": ["🌍🚀                                🛸", "🌍🚀            🛸", "🌍🚀🛸", "🌍💥Boom💥"],
    "knife": ["🔪                🎈", "🔪          🎈", "🔪🎈", "💥Boom💥"],
    "chaqmoq": ["☁️                ⚡️", "☁️         ⚡️", "☁️ ⚡️", "⛈"],
    "home": ["🏠              🚶‍♂", "🏠        🚶‍♂", "🏠🚶‍♂"],
    "ayriliq": ["❤️🧡💛💚", "💜💙🖤💛", "🤍🤎💛💜", "💚❤️🖤🧡", "💜💚🧡🖤"],
    "puq": ["💩               🤢", "💩     🤢", "💩 🤢", "🤮🤮"],
    "money": ["🔥                                 💵", "🔥                 💵", "🔥 💵", "💸"],
    "search": ["👽                     🔦😼", "👽          🔦😼", "👽🔦🙀"],
    "dance": ["🏡 💃", "🏡      💃", "🏡              💔👫", "🏡🚶‍♀"],
    "yurak": ["💗", "💓", "💖", "❤️", "💘", "💝", "💕"],
    "fuck": ["🤬", "😡", "🤬", "💢", "🤬", "💢💢", "🖕"],
}

# Delays for each animation
ANIM_DELAYS = {
    "love": 0.3, "xd": 0.3, "snow": 0.3, "police": 0.3, "kill": 0.3, "ari": 0.3,
    "load": 0.3, "god": 0.3, "snake": 0.3, "ghost": 0.1, "cosmo": 0.1, "knife": 0.2,
    "chaqmoq": 0.3, "home": 0.2, "ayriliq": 0.4, "puq": 0.3, "money": 0.1, "search": 0.1,
    "dance": 0.2, "yurak": 0.3, "fuck": 0.3
}

async def run_aiogram_animation(bot: Bot, chat_id: int, anim_name: str, conn_id: str = None):
    if anim_name not in ANIMATIONS:
        return
    
    frames = ANIMATIONS[anim_name]
    delay = ANIM_DELAYS.get(anim_name, 0.3)
    
    try:
        # Send first frame
        msg = await bot.send_message(
            chat_id=chat_id, 
            text=frames[0], 
            business_connection_id=conn_id, 
            parse_mode='HTML'
        )
        
        # Loop and edit
        for i in range(1, len(frames)):
            await asyncio.sleep(delay)
            try:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=msg.message_id,
                    text=frames[i],
                    business_connection_id=conn_id,
                    parse_mode='HTML'
                )
            except Exception:
                # Ignore edit errors (e.g. if message deleted or same text)
                pass
    except Exception as e:
        pass
