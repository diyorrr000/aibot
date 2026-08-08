import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta
from aiohttp import web
from aiogram import Bot
from app.config.settings import settings
from app.utils.logger import logger
from app.utils.helpers import to_bold_time, UZB_TZ
from app.database.connection import init_db, async_session
from app.database.repository import get_all_business_connections
from app.plugins.manager import plugin_manager
from app.keyboards.menu import register_bot_commands
from app.handlers.business import sync_all_business_connections
from app.bot import bot, dp

async def health_check(request):
    return web.Response(text="OK")

async def start_health_server():
    port = settings.port
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Health check HTTP server running on port {port}")

async def update_clock_task(bot_instance: Bot):
    while True:
        try:
            now_raw = datetime.now(UZB_TZ).strftime("%H:%M")
            try:
                await bot_instance.set_my_short_description(short_description=f"O'zbekiston vaqti: {now_raw}")
            except Exception as e:
                logger.debug(f"Bot short description clock failed: {e}")

            async with async_session() as session:
                conns = await get_all_business_connections(session)
                for conn in conns:
                    if not conn.clock_on and not conn.clock_bio_on:
                        continue
                    if conn.clock_on:
                        fn = conn.first_name or "User"
                        ln = (conn.last_name or "").strip()
                        new_last = f"{ln} | {to_bold_time(now_raw)}".strip(" |")
                        try:
                            await bot_instance.set_business_account_name(
                                business_connection_id=conn.connection_id,
                                first_name=fn,
                                last_name=new_last
                            )
                        except Exception as e:
                            logger.warning(f"Business name clock failed for {conn.connection_id}: {e}")
        except Exception as e:
            logger.error(f"Clock update task error: {e}")

        await asyncio.sleep(60)

async def auto_sync_business_task(bot_instance: Bot):
    """Periodically check and re-activate all business connections to handle redeployments seamlessly."""
    while True:
        try:
            await sync_all_business_connections(bot_instance)
        except Exception as e:
            logger.error(f"Business sync error: {e}")
        await asyncio.sleep(10)

async def main():
    logger.info("Bot starting up...")

    # Initialize Database
    await init_db()

    # Load Dynamic Plugins
    plugin_manager.load_plugins()

    # Start Health Check Server (Render requirement)
    await start_health_server()

    # Register Bot Menu Commands
    await register_bot_commands(bot)

    # Launch Background Sync & Clock Tasks
    asyncio.create_task(update_clock_task(bot))
    asyncio.create_task(auto_sync_business_task(bot))

    # Clear Webhook without dropping pending business updates
    logger.info("Clearing active webhook...")
    try:
        await bot.delete_webhook(drop_pending_updates=False)
    except Exception as e:
        logger.warning(f"delete_webhook failed: {e}")

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
            handle_signals=False
        )
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
