import time
import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from config import settings

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, limit: float = settings.rate_limit_seconds):
        self.limit = limit
        self.user_timestamps: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None

        if user_id:
            now = time.time()
            last_time = self.user_timestamps.get(user_id, 0)
            if now - last_time < self.limit:
                logger.warning(f"Rate limit exceeded for user_id={user_id}. Skipping processing.")
                return None  # Ignore rapid spam
            self.user_timestamps[user_id] = now

        return await handler(event, data)
