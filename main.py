import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import settings
from middlewares.rate_limit import RateLimitMiddleware
from handlers import commands, business_connection, business_message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("bot")


async def main():
    logger.info("Bot starting...")

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    dp = Dispatcher()

    dp.message.middleware(RateLimitMiddleware(limit=settings.rate_limit_seconds))
    dp.business_message.middleware(RateLimitMiddleware(limit=settings.rate_limit_seconds))

    dp.include_router(commands.router)
    dp.include_router(business_connection.router)
    dp.include_router(business_message.router)

    logger.info("Bot is live! Listening for updates...")
    await bot.delete_webhook(drop_pending_updates=True)

    allowed_updates = [
        "message",
        "edited_message",
        "business_connection",
        "business_message",
        "edited_business_message",
        "deleted_business_messages"
    ]

    try:
        await dp.start_polling(bot, allowed_updates=allowed_updates)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
