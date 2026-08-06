import logging
from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import BusinessConnectionModel, BusinessSettingsModel, ChatMessageModel

logger = logging.getLogger(__name__)

async def upsert_business_connection(
    session: AsyncSession,
    connection_id: str,
    user_id: int,
    user_chat_id: int,
    can_reply: bool,
    is_enabled: bool,
    rights: Optional[dict] = None
) -> BusinessConnectionModel:
    stmt = select(BusinessConnectionModel).where(BusinessConnectionModel.connection_id == connection_id)
    result = await session.execute(stmt)
    connection = result.scalar_one_or_none()

    if connection:
        connection.user_id = user_id
        connection.user_chat_id = user_chat_id
        connection.can_reply = can_reply
        connection.is_enabled = is_enabled
        connection.rights = rights
    else:
        connection = BusinessConnectionModel(
            connection_id=connection_id,
            user_id=user_id,
            user_chat_id=user_chat_id,
            can_reply=can_reply,
            is_enabled=is_enabled,
            rights=rights
        )
        session.add(connection)
    
    await session.commit()
    return connection

async def get_business_connection(
    session: AsyncSession, 
    connection_id: str
) -> Optional[BusinessConnectionModel]:
    stmt = select(BusinessConnectionModel).where(BusinessConnectionModel.connection_id == connection_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def get_business_connection_by_user(
    session: AsyncSession, 
    user_id: int
) -> Optional[BusinessConnectionModel]:
    stmt = select(BusinessConnectionModel).where(
        BusinessConnectionModel.user_id == user_id,
        BusinessConnectionModel.is_enabled == True
    ).order_by(BusinessConnectionModel.updated_at.desc())
    result = await session.execute(stmt)
    return result.scalars().first()

async def get_or_create_settings(
    session: AsyncSession,
    connection_id: str,
    user_id: int,
    default_prompt: str,
    default_model: str = "gpt-4o-mini"
) -> BusinessSettingsModel:
    stmt = select(BusinessSettingsModel).where(BusinessSettingsModel.connection_id == connection_id)
    result = await session.execute(stmt)
    settings_obj = result.scalar_one_or_none()

    if not settings_obj:
        settings_obj = BusinessSettingsModel(
            connection_id=connection_id,
            user_id=user_id,
            system_prompt=default_prompt,
            is_auto_reply_enabled=True,
            model_name=default_model
        )
        session.add(settings_obj)
        await session.commit()
    return settings_obj

async def update_settings(
    session: AsyncSession,
    connection_id: str,
    system_prompt: Optional[str] = None,
    is_auto_reply_enabled: Optional[bool] = None,
    model_name: Optional[str] = None
) -> Optional[BusinessSettingsModel]:
    stmt = select(BusinessSettingsModel).where(BusinessSettingsModel.connection_id == connection_id)
    result = await session.execute(stmt)
    settings_obj = result.scalar_one_or_none()

    if settings_obj:
        if system_prompt is not None:
            settings_obj.system_prompt = system_prompt
        if is_auto_reply_enabled is not None:
            settings_obj.is_auto_reply_enabled = is_auto_reply_enabled
        if model_name is not None:
            settings_obj.model_name = model_name
        await session.commit()
    return settings_obj

async def add_chat_message(
    session: AsyncSession,
    connection_id: str,
    chat_id: int,
    role: str,
    content: str
) -> ChatMessageModel:
    msg = ChatMessageModel(
        connection_id=connection_id,
        chat_id=chat_id,
        role=role,
        content=content
    )
    session.add(msg)
    await session.commit()
    return msg

async def get_chat_history(
    session: AsyncSession,
    connection_id: str,
    chat_id: int,
    limit: int = 20
) -> List[ChatMessageModel]:
    stmt = select(ChatMessageModel).where(
        ChatMessageModel.connection_id == connection_id,
        ChatMessageModel.chat_id == chat_id
    ).order_by(ChatMessageModel.id.desc()).limit(limit)
    
    result = await session.execute(stmt)
    messages = list(result.scalars().all())
    messages.reverse()  # Oldest to newest
    return messages

async def clear_chat_history(
    session: AsyncSession,
    connection_id: str,
    chat_id: int
):
    stmt = delete(ChatMessageModel).where(
        ChatMessageModel.connection_id == connection_id,
        ChatMessageModel.chat_id == chat_id
    )
    await session.execute(stmt)
    await session.commit()
