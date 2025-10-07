from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_proxy_menu() -> InlineKeyboardMarkup:
    # Упрощённое меню: одна загрузка (txt/текст, любые форматы), удаление по одному/все
    buttons = [
        [InlineKeyboardButton(text="📥 Загрузить прокси (txt/текст)", callback_data="proxy_load")],
        [InlineKeyboardButton(text="🗑️ Удалить", callback_data="proxy_delete")],
        [InlineKeyboardButton(text="❌ Удалить все", callback_data="proxy_delete_all")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_accounts_type_menu() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="👤 По логин/пароль", callback_data="accounts_loginpass"),
            InlineKeyboardButton(text="🍪 По cookie", callback_data="accounts_cookie"),
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_accounts_menu() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="📥 Загрузить (txt/текст)", callback_data="accounts_add"),
            InlineKeyboardButton(text="🗑️ Удалить", callback_data="accounts_delete"),
        ],
        [InlineKeyboardButton(text="❌ Удалить все", callback_data="accounts_delete_all")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="accounts_types")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_cookie_accounts_menu() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="➕ Загрузить cookie (.json/.txt)", callback_data="accounts_add_cookie")],
        [InlineKeyboardButton(text="🗑️ Удалить", callback_data="accounts_delete_cookie")],
        [InlineKeyboardButton(text="❌ Удалить все", callback_data="accounts_delete_all_cookie")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="accounts_types")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_back_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
        ]
    )

def get_delete_proxy_menu(proxies) -> InlineKeyboardMarkup:
    keyboard = []
    for idx, p in enumerate(proxies[:30], start=1):
        text = f"{idx}) {p[1]}:{p[2]}"
        keyboard.append([InlineKeyboardButton(text=text, callback_data=f"proxy_del_{p[0]}")])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_delete_account_menu(accounts) -> InlineKeyboardMarkup:
    keyboard = []
    for idx, a in enumerate(accounts[:30], start=1):
        text = f"{idx}) {a[1]}"
        keyboard.append([InlineKeyboardButton(text=text, callback_data=f"acc_del_{a[0]}")])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="accounts_types")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_delete_cookie_account_menu(cookie_accounts) -> InlineKeyboardMarkup:
    keyboard = []
    for idx, a in enumerate(cookie_accounts[:30], start=1):
        text = f"{idx}) {a[1]}"
        keyboard.append([InlineKeyboardButton(text=text, callback_data=f"cookie_del_{a[0]}")])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="accounts_types")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)