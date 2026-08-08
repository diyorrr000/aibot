from aiogram import Bot, types
from app.utils.logger import logger

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
