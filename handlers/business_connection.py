import logging
from aiogram import Router, types, Bot
from storage import get_conn_settings, set_conn_setting, ADMIN_ID

logger = logging.getLogger(__name__)
router = Router()

@router.business_connection()
async def handle_business_connection(business_connection: types.BusinessConnection, bot: Bot):
    conn_id = business_connection.id
    user_id = business_connection.user.id
    is_enabled = business_connection.is_enabled
    can_reply = business_connection.can_reply

    user = business_connection.user
    raw_username = user.username
    if raw_username:
        username = f"@{raw_username}"
    else:
        username = user.full_name or "akkount egasi"

    # Save connection (is_approved=False — admin must approve first)
    set_conn_setting(
        conn_id,
        user_id=user_id,
        can_reply=can_reply,
        is_enabled=False,         # Disabled until admin approves
        is_approved=False,        # Must be approved by admin
        username=username,
        first_name=user.first_name or "",
        last_name=user.last_name or ""
    )

    logger.info(
        f"Business Connection: conn_id={conn_id}, user_id={user_id}, username={username}, "
        f"is_enabled={is_enabled}, can_reply={can_reply}"
    )

    # Notify admin for approval
    try:
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"🔔 YANGI ULANISH!\n\n"
                f"Foydalanuvchi: {username}\n"
                f"User ID: {user_id}\n"
                f"Connection ID: {conn_id}\n\n"
                f"Ruxsat berish uchun:\n/approve {conn_id}\n\n"
                f"Rad etish uchun:\n/disapprove {conn_id}"
            ),
            parse_mode=None
        )
    except Exception as e:
        logger.warning(f"Could not notify admin about new connection: {e}")

    # Notify user that they are waiting for approval
    try:
        await bot.send_message(
            chat_id=user_id,
            text=(
                f"✅ Business hisob ulandi!\n\n"
                f"Hisob: {username}\n\n"
                f"⏳ Bot admin tomonidan tasdiqlanishini kuting.\n"
                f"Tasdiqlangandan keyin Business xabarlaringizga avtomatik javob beriladi."
            ),
            parse_mode=None
        )
    except Exception as e:
        logger.warning(f"Could not notify user about pending approval: {e}")
