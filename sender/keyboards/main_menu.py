from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="🚀 Старт рассылка", callback_data="start_mailing")],
        [InlineKeyboardButton(text="🧑‍💻 Управление браузерами", callback_data="manage_browsers")],
        [
            InlineKeyboardButton(text="🌐 Прокси", callback_data="proxy"),
            InlineKeyboardButton(text="👤 Аккаунты", callback_data="accounts")
        ],
        [InlineKeyboardButton(text="📋 Площадки для ворка", callback_data="work_platforms")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_back_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
        ]
    )

def get_browser_control_keyboard(status: str) -> InlineKeyboardMarkup:
    """Клавиатура для одного браузера"""
    buttons = []
    if status == "running":
        buttons.append([InlineKeyboardButton(text="⏸ Пауза", callback_data="pause_browser")])
    else:
        buttons.append([InlineKeyboardButton(text="▶ Продолжить", callback_data="resume_browser")])
    buttons.append([InlineKeyboardButton(text="❌ Закрыть", callback_data="close_browser")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_manage_browsers_keyboard(has_browsers: bool) -> InlineKeyboardMarkup:
    """Старый вариант — оставляем для совместимости."""
    buttons = []
    if has_browsers:
        buttons.append([InlineKeyboardButton(text="🛑 Закрыть все", callback_data="close_all_browsers")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_manage_browsers_list_keyboard(active_browsers: dict) -> InlineKeyboardMarkup:
    """
    Новый вариант — список сессий + кнопки на каждую: Пауза/Продолжить/Закрыть.
    Колбэки: pause_browser_id:{id}, resume_browser_id:{id}, close_browser_id:{id}
    """
    rows = []
    if active_browsers:
        for bid, data in active_browsers.items():
            status = data.get("status", "running")
            title = f"#{bid} | {data.get('platform','').upper()} | {data.get('username') or 'Без аккаунта'}"
            status_txt = "⏸ Приостановлен" if status == "paused" else "▶️ Работает"
            rows.append([InlineKeyboardButton(text=f"🧭 {title} [{status_txt}]", callback_data="noop")])
            btns = []
            if status == "running":
                btns.append(InlineKeyboardButton(text="⏸ Пауза", callback_data=f"pause_browser_id:{bid}"))
            elif status == "paused":
                btns.append(InlineKeyboardButton(text="▶️ Продолжить", callback_data=f"resume_browser_id:{bid}"))
            btns.append(InlineKeyboardButton(text="❌ Закрыть", callback_data=f"close_browser_id:{bid}"))
            rows.append(btns)
        rows.append([InlineKeyboardButton(text="🛑 Закрыть все", callback_data="close_all_browsers")])
    rows.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)