import logging
from aiogram import Router, types
from storage import get_conn_settings, set_conn_setting

logger = logging.getLogger(__name__)
router = Router()

@router.business_connection()
async def handle_business_connection(business_connection: types.BusinessConnection):
    conn_id = business_connection.id
    user_id = business_connection.user.id
    is_enabled = business_connection.is_enabled
    can_reply = business_connection.can_reply

    set_conn_setting(
        conn_id,
        user_id=user_id,
        can_reply=can_reply,
        is_enabled=is_enabled
    )

    logger.info(
        f"Business Connection: conn_id={conn_id}, user_id={user_id}, "
        f"is_enabled={is_enabled}, can_reply={can_reply}"
    )
