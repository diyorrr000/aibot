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

from datetime import datetime, timezone, timedelta
from storage import is_clock_enabled, connection_settings

BOLD_DIGITS = {
    '0': '𝟎', '1': '𝟏', '2': '𝟐', '3': '𝟑', '4': '𝟒',
    '5': '𝟓', '6': '𝟔', '7': '𝟕', '8': '𝟖', '9': '𝟗',
    ':': ':'
}

def to_bold_time(time_str: str) -> str:
    return "".join(BOLD_DIGITS.get(c, c) for c in time_str)


async def update_clock_task(bot: Bot):
    uzb_tz = timezone(timedelta(hours=5))
    while True:
        try:
            if is_clock_enabled():
                now_raw = datetime.now(uzb_tz).strftime("%H:%M")
                bold_time = to_bold_time(now_raw)

                # Update bot's short description
                try:
                    await bot.set_my_short_description(short_description=f"O'zbekiston vaqti: {now_raw}")
                except Exception as e:
                    logger.debug(f"Bot short description clock failed: {e}")

                # Update connected business profile last_name with bold time (e.g. 𝟏𝟗:𝟓𝟓)
                for conn_id, conn in list(connection_settings.items()):
                    if conn.get("is_enabled") and conn.get("user_id"):
                        fn = conn.get("first_name") or "User"
                        try:
                            await bot.set_business_account_name(
                                business_connection_id=conn_id,
                                first_name=fn,
                                last_name=bold_time
                            )
                        except Exception as e:
                            logger.warning(f"Business account name clock failed for {conn_id}: {e}")
        except Exception as e:
            logger.error(f"Clock update task error: {e}")

        await asyncio.sleep(60)


async def main():
    logger.info("Bot starting...")

    # Start HTTP health check server (required by Render Web Service)
    await start_health_server()

    logger.info("Claude Haiku (KILWA API) ready — no pre-init needed.")

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=None)
    )
    dp = Dispatcher()

    dp.message.middleware(RateLimitMiddleware(limit=settings.rate_limit_seconds))
    dp.business_message.middleware(RateLimitMiddleware(limit=settings.rate_limit_seconds))

    dp.include_router(commands.router)
    dp.include_router(business_connection.router)
    dp.include_router(business_message.router)

    # Launch Uzbekistan auto-clock background task
    asyncio.create_task(update_clock_task(bot))

    # ── Conflict-proof startup ──────────────────────────────────────────
    # 1. Delete any active webhook (clears both webhook AND long-poll locks)
    logger.info("Clearing any existing webhook or active polling sessions...")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook cleared successfully.")
    except Exception as e:
        logger.warning(f"delete_webhook failed: {e}")

    # 2. Wait for old Render instance to fully shut down (Render overlaps ~5-10s)
    logger.info("Waiting 8 seconds to let any previous instance stop...")
    await asyncio.sleep(8)

    # 3. Delete webhook again to be sure (second call is safe and idempotent)
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception:
        pass

    allowed_updates = [
        "message",
        "edited_message",
        "callback_query",
        "business_connection",
        "business_message",
        "edited_business_message",
        "deleted_business_messages"
    ]

    logger.info("Bot is live! Listening for updates...")
    try:
        await dp.start_polling(
            bot,
            allowed_updates=allowed_updates,
            polling_timeout=30,
            handle_signals=False,
        )
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
