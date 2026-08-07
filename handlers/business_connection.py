import logging
from aiogram import Router, types, Bot
from storage import get_conn_settings, set_conn_setting, clear_other_connections, ADMIN_ID

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

    # Only the admin's own business account is served. Other accounts are
    # stored but never activated, so the bot can't be used by anyone else.
    is_admin_conn = (user_id == ADMIN_ID)

    # Only the NEWEST connection is kept — old/stale connections are deleted.
    if is_admin_conn:
        clear_other_connections(conn_id)

    set_conn_setting(
        conn_id,
        user_id=user_id,
        can_reply=can_reply,
        is_enabled=is_enabled and is_admin_conn,
        is_approved=is_admin_conn,
        username=username,
        first_name=user.first_name or "",
        last_name=user.last_name or ""
    )

    logger.info(
        f"Business Connection: conn_id={conn_id}, user_id={user_id}, username={username}, "
        f"is_enabled={is_enabled}, can_reply={can_reply}, is_admin_conn={is_admin_conn}"
    )

    if is_admin_conn:
        # Admin's own account — works immediately, no approval needed
        try:
            await bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"✅ Business hisob ulandi!\n\n"
                    f"Hisob: {username}\n"
                    f"User ID: {user_id}\n\n"
                    f"Endi ushbu akkuntga kelgan xabarlarga avtomatik javob beriladi.\n"
                    f"Tasdiqlash shart emas — bot darhol ishlaydi."
                ),
                parse_mode=None
            )
        except Exception as e:
            logger.warning(f"Could not notify admin about connection: {e}")
    else:
        try:
            await bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"⚠️ Yangi ulanish, lekin bot FAQAT admin akkunti uchun ishlaydi.\n\n"
                    f"Foydalanuvchi: {username}\n"
                    f"User ID: {user_id}\n"
                    f"Bu akkunt uchun bot ishga tushirilmaydi."
                ),
                parse_mode=None
            )
        except Exception as e:
            logger.warning(f"Could not notify admin about non-admin connection: {e}")
        try:
            await bot.send_message(
                chat_id=user_id,
                text=(
                    f"❌ Kechirasiz, bu bot faqat admin akkunti uchun ishlaydi.\n"
                    f"Sizning Telegram Business ulanishingiz ishga tushirilmaydi."
                ),
                parse_mode=None
            )
        except Exception as e:
            logger.warning(f"Could not notify non-admin user: {e}")
