from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(text="🤖 Gemini 2.5 Flash AI", callback_data="nav:ai"),
            InlineKeyboardButton(text="🎛 AI Sozlamalar", callback_data="nav:models")
        ],
        [
            InlineKeyboardButton(text="🧩 Plaginlar", callback_data="nav:plugins"),
            InlineKeyboardButton(text="💼 Business", callback_data="nav:business")
        ],
        [
            InlineKeyboardButton(text="👤 Profil", callback_data="nav:profile"),
            InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data="nav:settings")
        ],
        [
            InlineKeyboardButton(text="📖 Yordam", callback_data="nav:help")
        ]
    ]
    if is_admin:
        kb.append([
            InlineKeyboardButton(text="👑 Admin Panel", callback_data="nav:admin")
        ])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_breadcrumbs_keyboard(back_target: str = "home") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="← Orqaga", callback_data=f"nav:{back_target}"),
            InlineKeyboardButton(text="🏠 Bosh sahifa", callback_data="nav:home")
        ]
    ])

def get_settings_keyboard(user_id: int, is_admin: bool, conn_id: str = "", current_model: str = "gemini", is_enabled: bool = True, clock_enabled: bool = False) -> InlineKeyboardMarkup:
    kb = []
    if is_admin:
        clock_st = "🟢 YOQILGAN" if clock_enabled else "🔴 O'CHIRILGAN"
        kb.append([InlineKeyboardButton(text=f"🕒 Global Soat: {clock_st}", callback_data="action:toggle_global_clock")])

    if conn_id:
        kb.append([
            InlineKeyboardButton(text="✅ ⚡ Gemini 2.5 Flash (Cheksiz va Bepul)", callback_data=f"set_model:{conn_id}:gemini")
        ])
        auto_st = "🟢 Avto-Javob: YOQILGAN" if is_enabled else "🔴 Avto-Javob: O'CHIRILGAN"
        kb.append([InlineKeyboardButton(text=auto_st, callback_data=f"action:toggle_auto:{conn_id}")])

    kb.append([
        InlineKeyboardButton(text="🗑 Tarixni tozalash", callback_data="action:clear_history"),
        InlineKeyboardButton(text="🔄 Yangilash", callback_data="nav:settings")
    ])
    kb.append([
        InlineKeyboardButton(text="← Orqaga", callback_data="nav:home"),
        InlineKeyboardButton(text="🏠 Bosh sahifa", callback_data="nav:home")
    ])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Ulangan Hisoblar", callback_data="admin:connections"),
            InlineKeyboardButton(text="🧹 Barchasini Tozalash", callback_data="admin:clear_all")
        ],
        [
            InlineKeyboardButton(text="← Orqaga", callback_data="nav:home"),
            InlineKeyboardButton(text="🏠 Bosh sahifa", callback_data="nav:home")
        ]
    ])
