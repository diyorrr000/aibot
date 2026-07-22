import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import settings
from database.connection import init_db
from middlewares.db_session import DbSessionMiddleware
from middlewares.rate_limit import RateLimitMiddleware
from handlers import commands, business_connection, business_message

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("telegram_business_bot")

async def main():
    logger.info("Starting Telegram Business AI Bot initialization...")

    # 1. Initialize Database
    await init_db()

    # 2. Initialize Bot and Dispatcher
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    dp = Dispatcher()

    # 3. Attach Middlewares
    dp.update.outer_middleware(DbSessionMiddleware())
    dp.message.middleware(RateLimitMiddleware(limit=settings.rate_limit_seconds))
    dp.business_message.middleware(RateLimitMiddleware(limit=settings.rate_limit_seconds))

    # 4. Include Routers
    dp.include_router(commands.router)
    dp.include_router(business_connection.router)
    dp.include_router(business_message.router)

    # 5. Start Polling
    logger.info("Bot is active and listening for updates (including Telegram Business messages)...")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        allowed_updates = [
            "message",
            "edited_message",
            "business_connection",
            "business_message",
            "edited_business_message",
            "deleted_business_messages"
        ]
        await dp.start_polling(bot, allowed_updates=allowed_updates)
    except Exception as e:
        logger.critical(f"Critical error in main loop: {e}", exc_info=True)
    finally:
        logger.info("Shutting down bot session...")
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped successfully.")
