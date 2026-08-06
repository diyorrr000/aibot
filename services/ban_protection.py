import asyncio
import random
import logging
from telethon import errors

logger = logging.getLogger("ban_protection")

class BanProtectionGuard:
    """
    Telegram Account Anti-Ban & Safety Manager.
    Enforces human behavior simulation, rate limits, random delays,
    and automatic FloodWait handling to protect user accounts from bans.
    """

    def __init__(self):
        self.enabled = True
        self.min_delay = 1.5
        self.max_delay = 3.5

    async def random_sleep(self, min_s: float = None, max_s: float = None):
        """Add random human-like delay between requests."""
        if not self.enabled:
            return
        low = min_s if min_s is not None else self.min_delay
        high = max_s if max_s is not None else self.max_delay
        delay = random.uniform(low, high)
        await asyncio.sleep(delay)

    async def safe_execute(self, coro, default=None):
        """
        Safely execute a Telethon request with FloodWait catching and auto-retry.
        """
        try:
            return await coro
        except errors.FloodWaitError as e:
            logger.warning(f"🛡 [Anti-Ban] Telegram FloodWait detected: sleeping for {e.seconds + 2}s")
            await asyncio.sleep(e.seconds + 2)
            try:
                return await coro
            except Exception as ex:
                logger.error(f"🛡 [Anti-Ban] Execution failed after FloodWait: {ex}")
                return default
        except errors.UserBannedInChannelError:
            logger.warning("🛡 [Anti-Ban] Action prevented: User restricted in channel.")
            return default
        except errors.PeerFloodError:
            logger.error("🛡 [Anti-Ban] PeerFloodError! Throttling all automated messages for 60 seconds.")
            await asyncio.sleep(60)
            return default
        except Exception as e:
            logger.error(f"🛡 [Anti-Ban] Telethon API error: {e}")
            return default

    async def safe_broadcast_delay(self):
        """Enforce strict 8 to 14 second delay between broadcast messages to avoid spam bans."""
        await self.random_sleep(8.0, 14.0)

    async def safe_animation_delay(self):
        """Enforce 1.2s delay between animation frame edits."""
        await asyncio.sleep(1.2)


ban_guard = BanProtectionGuard()
