import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

logger = logging.getLogger("middleware.error")

class GlobalErrorMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            logger.error(f"Global unhandled exception: {e}", exc_info=True)
            if isinstance(event, Message):
                try:
                    await event.answer("🚫 Xatolik yuz berdi. Qayta urinib ko'ring.", parse_mode=None)
                except Exception:
                    pass
            elif isinstance(event, CallbackQuery):
                try:
                    await event.answer("🚫 Xatolik yuz berdi!", show_alert=True)
                except Exception:
                    pass
            return None
