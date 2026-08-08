import time
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from app.config.settings import settings

class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, limit: float = settings.rate_limit_seconds):
        self.limit = limit
        self.last_time: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else 0
            if user_id:
                now = time.time()
                last = self.last_time.get(user_id, 0)
                if now - last < self.limit:
                    return None
                self.last_time[user_id] = now
        return await handler(event, data)
