import logging
from typing import List, Optional, Dict, Any
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import BusinessConnectionModel, ChatMessageModel, ChatModelPinModel, GreetingDateModel

logger = logging.getLogger(__name__)

async def upsert_business_connection(
    session: AsyncSession,
    connection_id: str,
    user_id: int,
    user_chat_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    can_reply: bool = True,
    is_enabled: bool = True,
    is_approved: bool = True,
    model: str = "claude",
    system_prompt: Optional[str] = None,
    rights: Optional[dict] = None
) -> BusinessConnectionModel:
    stmt = select(BusinessConnectionModel).where(BusinessConnectionModel.connection_id == connection_id)
    result = await session.execute(stmt)
    connection = result.scalar_one_or_none()

    if connection:
        connection.user_id = user_id
        connection.user_chat_id = user_chat_id
        if username is not None: connection.username = username
        if first_name is not None: connection.first_name = first_name
        if last_name is not None: connection.last_name = last_name
        connection.can_reply = can_reply
        connection.is_enabled = is_enabled
        connection.is_approved = is_approved
        if model: connection.model = model
        if system_prompt: connection.system_prompt = system_prompt
        if rights: connection.rights = rights
    else:
        connection = BusinessConnectionModel(
            connection_id=connection_id,
            user_id=user_id,
            user_chat_id=user_chat_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            can_reply=can_reply,
            is_enabled=is_enabled,
            is_approved=is_approved,
            model=model,
            system_prompt=system_prompt,
            rights=rights
        )
        session.add(connection)

    await session.commit()
    return connection

async def get_business_connection(session: AsyncSession, connection_id: str) -> Optional[BusinessConnectionModel]:
    stmt = select(BusinessConnectionModel).where(BusinessConnectionModel.connection_id == connection_id)
    res = await session.execute(stmt)
    return res.scalar_one_or_none()

async def get_all_business_connections(session: AsyncSession) -> List[BusinessConnectionModel]:
    stmt = select(BusinessConnectionModel)
    res = await session.execute(stmt)
    return list(res.scalars().all())

async def get_user_connection(session: AsyncSession, user_id: int) -> Optional[BusinessConnectionModel]:
    stmt = select(BusinessConnectionModel).where(
        BusinessConnectionModel.user_id == user_id
    ).order_by(BusinessConnectionModel.updated_at.desc())
    res = await session.execute(stmt)
    return res.scalars().first()

async def remove_stale_user_connections(session: AsyncSession, user_id: int, keep_conn_id: str):
    stmt = delete(BusinessConnectionModel).where(
        BusinessConnectionModel.user_id == user_id,
        BusinessConnectionModel.connection_id != keep_conn_id
    )
    await session.execute(stmt)
    await session.commit()

async def update_conn_settings(session: AsyncSession, connection_id: str, **kwargs):
    conn = await get_business_connection(session, connection_id)
    if conn:
        for k, v in kwargs.items():
            if hasattr(conn, k):
                setattr(conn, k, v)
        await session.commit()
    return conn

async def add_chat_message(session: AsyncSession, connection_id: str, chat_id: int, role: str, content: str):
    msg = ChatMessageModel(
        connection_id=connection_id,
        chat_id=chat_id,
        role=role,
        content=content
    )
    session.add(msg)
    await session.commit()
    return msg

async def get_chat_history(session: AsyncSession, connection_id: str, chat_id: int, limit: int = 20) -> List[ChatMessageModel]:
    stmt = select(ChatMessageModel).where(
        ChatMessageModel.connection_id == connection_id,
        ChatMessageModel.chat_id == chat_id
    ).order_by(ChatMessageModel.id.desc()).limit(limit)
    res = await session.execute(stmt)
    msgs = list(res.scalars().all())
    msgs.reverse()
    return msgs

async def clear_chat_history(session: AsyncSession, chat_id: int):
    stmt = delete(ChatMessageModel).where(ChatMessageModel.chat_id == chat_id)
    await session.execute(stmt)
    await session.commit()

async def get_pinned_chat_model(session: AsyncSession, connection_id: str, chat_id: int) -> Optional[str]:
    stmt = select(ChatModelPinModel).where(
        ChatModelPinModel.connection_id == connection_id,
        ChatModelPinModel.chat_id == chat_id
    )
    res = await session.execute(stmt)
    pin = res.scalar_one_or_none()
    return pin.model_name if pin else None

async def set_pinned_chat_model(session: AsyncSession, connection_id: str, chat_id: int, model_name: str):
    stmt = select(ChatModelPinModel).where(
        ChatModelPinModel.connection_id == connection_id,
        ChatModelPinModel.chat_id == chat_id
    )
    res = await session.execute(stmt)
    pin = res.scalar_one_or_none()
    if pin:
        pin.model_name = model_name
    else:
        pin = ChatModelPinModel(connection_id=connection_id, chat_id=chat_id, model_name=model_name)
        session.add(pin)
    await session.commit()

async def get_greeting_date(session: AsyncSession, chat_id: int) -> str:
    stmt = select(GreetingDateModel).where(GreetingDateModel.chat_id == chat_id)
    res = await session.execute(stmt)
    g = res.scalar_one_or_none()
    return g.last_greeting_date if g else ""

async def set_greeting_date(session: AsyncSession, chat_id: int, date_str: str):
    stmt = select(GreetingDateModel).where(GreetingDateModel.chat_id == chat_id)
    res = await session.execute(stmt)
    g = res.scalar_one_or_none()
    if g:
        g.last_greeting_date = date_str
    else:
        g = GreetingDateModel(chat_id=chat_id, last_greeting_date=date_str)
        session.add(g)
    await session.commit()
