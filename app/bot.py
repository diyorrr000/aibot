from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from app.config.settings import settings
from app.handlers import start_router, admin_router, business_router
from app.middlewares.rate_limit import RateLimitMiddleware
from app.middlewares.error_handler import GlobalErrorMiddleware

bot = Bot(
    token=settings.bot_token,
    default=DefaultBotProperties(parse_mode=None)
)

dp = Dispatcher()

# Middlewares
dp.message.middleware(GlobalErrorMiddleware())
dp.callback_query.middleware(GlobalErrorMiddleware())
dp.message.middleware(RateLimitMiddleware(limit=settings.rate_limit_seconds))

# Routers
dp.include_router(start_router)
dp.include_router(admin_router)
dp.include_router(business_router)
