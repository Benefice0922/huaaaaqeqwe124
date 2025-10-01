from aiogram import types

def get_countries_menu():
    """Клавиатура для выбора страны"""
    kb = [
        [
            types.InlineKeyboardButton(text="🇰🇿 Казахстан", callback_data="country_kz")
        ],
        [
            types.InlineKeyboardButton(text="🇰🇬 Киргизия", callback_data="country_kg")
        ],
        [
            types.InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")
        ]
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=kb)

def get_platforms_menu(country="kz"):
    """Клавиатура для выбора платформы в зависимости от страны"""
    kb = []
    
    if country == "kz":
        kb = [
            [
                types.InlineKeyboardButton(text="🏢 Krisha.kz", callback_data="krisha")
            ],
            [
                types.InlineKeyboardButton(text="🚗 Kolesa.kz", callback_data="kolesa")
            ],
            [
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_countries")
            ]
        ]
    elif country == "kg":
        kb = [
            [
                types.InlineKeyboardButton(text="🛒 Lalafo.kg", callback_data="lalafo")
            ],
            [
                types.InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_countries")
            ]
        ]
    
    return types.InlineKeyboardMarkup(inline_keyboard=kb)

def get_platform_settings_menu(platform, settings):
    """Клавиатура настроек платформы — первая строка кастомный текст, вторая лимиты, остальное по одной"""
    multithread_status = "✅" if settings.get("multithread", False) else "❌"
    keyboard = [
        [  # Первая строка: только кастомный текст
            types.InlineKeyboardButton(
                text="📝 Кастомный текст",
                callback_data=f"edit_custom_text_{platform}"
            ),
        ],
        [  # Вторая строка: лимит отписок и лимит прокси
            types.InlineKeyboardButton(
                text="📩 Лимит отписок",
                callback_data=f"edit_max_unsubscribes_{platform}"
            ),
            types.InlineKeyboardButton(
                text="🌐 Лимит прокси",
                callback_data=f"edit_max_proxies_per_account_{platform}"
            ),
        ],
        [  # Третья строка: Количество браузеров
            types.InlineKeyboardButton(
                text="💻 Количество браузеров",
                callback_data=f"edit_browser_count_{platform}"
            ),
        ],
        [  # Четвертая строка: Категории
            types.InlineKeyboardButton(
                text="🏷️ Категории",
                callback_data=f"edit_categories_{platform}"
            ),
        ],
        [  # Пятая строка: Доп. селекторы
            types.InlineKeyboardButton(
                text="🔎 Доп. селекторы",
                callback_data=f"edit_selectors_{platform}"
            ),
        ],
        [  # Шестая строка: Мультипоток
            types.InlineKeyboardButton(
                text=f"🔄 Мультипоток {multithread_status}",
                callback_data=f"toggle_multithread_{platform}"
            ),
        ],
        [  # Последняя строка: Назад к площадкам
            types.InlineKeyboardButton(
                text="⬅️ Назад к площадкам",
                callback_data="platforms"
            )
        ]
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=keyboard)