from aiogram import Bot, types
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from app.utils.logger import logger

def get_main_reply_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text="🤖 Gemini 2.5 Flash AI"),
            KeyboardButton(text="🎛 AI Sozlamalar")
        ],
        [
            KeyboardButton(text="🧩 Plaginlar va Buyruqlar"),
            KeyboardButton(text="💼 Business Ulanish")
        ],
        [
            KeyboardButton(text="👤 Profilim"),
            KeyboardButton(text="⚙️ Sozlamalar")
        ],
        [
            KeyboardButton(text="📖 Yordam")
        ]
    ]
    if is_admin:
        kb.append([KeyboardButton(text="👑 Admin Panel")])

    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

async def register_bot_commands(bot: Bot):
    try:
        commands = [
            types.BotCommand(command="start", description="🏠 Boshqaruv paneli"),
            types.BotCommand(command="settings", description="⚙️ Bot sozlamalari"),
            types.BotCommand(command="profile", description="👤 Profil ma'lumotlari"),
            types.BotCommand(command="help", description="📖 Yordam markazi"),
            types.BotCommand(command="admin", description="👑 Admin panel"),
        ]
        await bot.set_my_commands(commands)
        logger.info("Registered bot command menu successfully.")
    except Exception as e:
        logger.warning(f"Failed to register bot command menu: {e}")
