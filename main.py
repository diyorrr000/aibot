import asyncio
import logging
import sys
import os
from aiohttp import web
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

async def health_check(request):
    return web.Response(text="OK")

async def start_health_server():
    port = int(os.getenv("PORT", 3000))
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Health check server running on port {port}")

async def main():
    logger.info("Bot starting...")

    # Start HTTP health check server (required by Render Web Service)
    await start_health_server()

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

    # Drop pending updates and delete webhook to avoid conflicts
    await bot.delete_webhook(drop_pending_updates=True)

    allowed_updates = [
        "message",
        "edited_message",
        "business_connection",
        "business_message",
        "edited_business_message",
        "deleted_business_messages"
    ]

    logger.info("Bot is live! Listening for updates...")
    try:
        await dp.start_polling(bot, allowed_updates=allowed_updates)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
