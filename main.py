import asyncio
import logging
import sys
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types
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
from storage import is_clock_enabled, connection_settings, to_bold_time


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

            # Update connected business profiles where the owner enabled .soat / .soatbio
            for conn_id, conn in list(connection_settings.items()):
                if not conn.get("user_id"):
                    continue
                clock_on = conn.get("clock")
                bio_on = conn.get("clock_bio")
                if not clock_on and not bio_on:
                    continue
                now_raw = datetime.now(uzb_tz).strftime("%H:%M")
                if clock_on:
                    fn = conn.get("orig_first_name") or conn.get("first_name") or "User"
                    ln = (conn.get("orig_last_name") or conn.get("last_name") or "").strip()
                    new_last = f"{ln} | 🕒 {to_bold_time(now_raw)}".strip(" |")
                    try:
                        await bot.set_business_account_name(
                            business_connection_id=conn_id,
                            first_name=fn,
                            last_name=new_last
                        )
                    except Exception as e:
                        logger.warning(f"Business name clock failed for {conn_id}: {e}")
                if bio_on and hasattr(bot, "set_business_account_bio"):
                    try:
                        now_date = datetime.now(uzb_tz).strftime("%d.%m.%Y")
                        bio = f"🕒 Soat: {to_bold_time(now_raw)} | 📅 Sana: {now_date}"
                        await bot.set_business_account_bio(business_connection_id=conn_id, bio=bio)
                    except Exception as e:
                        logger.warning(f"Business bio clock failed for {conn_id}: {e}")
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
    # NOTE: no rate-limit middleware on business_message — it silently dropped
    # owner commands and customer messages. Commands always work; the auto-reply
    # has its own per-chat cooldown in the handler.

    dp.include_router(commands.router)
    dp.include_router(business_connection.router)
    dp.include_router(business_message.router)

    # Telegram "MENU" button — easy access to the admin panel without inline keys
    try:
        await bot.set_my_commands([
            types.BotCommand(command="start", description="🏠 Boshqaruv paneli"),
            types.BotCommand(command="settings", description="⚙️ Bot sozlamalari"),
            types.BotCommand(command="connections", description="📋 Ulangan akkuntlar"),
            types.BotCommand(command="approve", description="✅ Akkuntni tasdiqlash"),
            types.BotCommand(command="disapprove", description="❌ Akkuntni rad etish"),
            types.BotCommand(command="reset", description="🗑 Tarixni tozalash"),
            types.BotCommand(command="help", description="📖 Yordam"),
        ])
        logger.info("Bot command menu (MENU button) registered.")
    except Exception as e:
        logger.warning(f"set_my_commands failed: {e}")

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
