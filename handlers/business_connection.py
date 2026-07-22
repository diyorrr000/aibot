import logging
from aiogram import Router, types
from sqlalchemy.ext.asyncio import AsyncSession
from database.repository import upsert_business_connection, get_or_create_settings
from config import settings

logger = logging.getLogger(__name__)
router = Router()

@router.business_connection()
async def handle_business_connection(
    business_connection: types.BusinessConnection,
    session: AsyncSession
):
    """
    Triggered when a user connects/disconnects the bot in Telegram Business Settings -> Chat Bots.
    """
    conn_id = business_connection.id
    user_id = business_connection.user.id
    user_chat_id = business_connection.user_chat_id
    can_reply = business_connection.can_reply
    is_enabled = business_connection.is_enabled
    
    rights = {
        "can_reply": can_reply,
        "is_enabled": is_enabled,
        "date": business_connection.date.isoformat() if business_connection.date else None
    }

    logger.info(
        f"Business Connection Update: conn_id={conn_id}, user_id={user_id}, "
        f"can_reply={can_reply}, is_enabled={is_enabled}"
    )

    # Save or update connection status in DB
    await upsert_business_connection(
        session=session,
        connection_id=conn_id,
        user_id=user_id,
        user_chat_id=user_chat_id,
        can_reply=can_reply,
        is_enabled=is_enabled,
        rights=rights
    )

    # Initialize default settings for this connection if enabled
    if is_enabled:
        await get_or_create_settings(
            session=session,
            connection_id=conn_id,
            user_id=user_id,
            default_prompt=settings.default_system_prompt,
            default_model=settings.default_model
        )
