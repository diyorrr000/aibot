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

    # Keep only this user's NEWEST connection — their older/stale ones are removed.
    # Other users' connections are untouched.
    clear_other_connections(conn_id, keep_user_id=user_id)

    # EVERY user who connects the bot gets it working immediately — no approval.
    # is_enabled is forced True: a False value in a Telegram connection update
    # (or a stale persisted one) would otherwise silently stop every reply.
    set_conn_setting(
        conn_id,
        user_id=user_id,
        can_reply=can_reply,
        is_enabled=True,
        is_approved=True,
        username=username,
        first_name=user.first_name or "",
        last_name=user.last_name or ""
    )

    logger.info(
        f"Business Connection: conn_id={conn_id}, user_id={user_id}, username={username}, "
        f"is_enabled={is_enabled}, can_reply={can_reply}"
    )

    # Notify the user that their account is now served
    try:
        await bot.send_message(
            chat_id=user_id,
            text=(
                f"✅ Telegram Business hisobingiz botga ulandi!\n\n"
                f"👤 Hisob: {username}\n\n"
                f"Endi ushbu akkuntga kelgan xabarlarga avtomatik javob beriladi.\n"
                f"📋 Buyruqlar ro'yxati: .help\n"
                f"⚙️ Sozlamalar: /settings"
            ),
            parse_mode=None
        )
    except Exception as e:
        logger.warning(f"Could not notify user {user_id} about connection: {e}")

    # Inform the admin (informational only)
    if user_id != ADMIN_ID:
        try:
            await bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"🔗 Yangi Business ulanish!\n\n"
                    f"👤 Foydalanuvchi: {username}\n"
                    f"🆔 User ID: {user_id}\n\n"
                    f"Avtomatik faollashtirildi."
                ),
                parse_mode=None
            )
        except Exception as e:
            logger.warning(f"Could not notify admin about connection: {e}")
