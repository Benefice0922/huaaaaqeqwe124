from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def _on_off(flag: bool, on: str = "✅ Вкл", off: str = "❌ Выкл") -> str:
    return on if flag else off

def get_settings_menu(settings: dict) -> InlineKeyboardMarkup:
    """Главное меню настроек с кнопкой API"""
    
    # Проверяем статус API
    api_configured = False
    api_emoji = "❌"
    
    try:
        import json
        import os
        if os.path.exists('settings.json'):
            with open('settings.json', 'r', encoding='utf-8') as f:
                saved_settings = json.load(f)
                api_settings = saved_settings.get("api_settings", {})
                if api_settings.get("bastart_project_token") and api_settings.get("bastart_worker_token"):
                    api_configured = True
                    api_emoji = "✅"
    except:
        pass
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🕵️ Антидетект", callback_data="open_fingerprint_settings")],
            [InlineKeyboardButton(text="⚙️ Общие", callback_data="open_common_settings")],
            [InlineKeyboardButton(text=f"🔗 Настройки API", callback_data="open_api_settings")],
            [InlineKeyboardButton(text="⏱ Автозапуск", callback_data="open_autostart_settings")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")],
        ]
    )

def get_common_menu(settings: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"Видимость браузера: {'👁️ Видим' if settings.get('browser_visible', False) else '🙈 Скрыт'}", 
                callback_data="toggle_browser_visible"
            )],
            [InlineKeyboardButton(
                text=f"Работа без прокси: {_on_off(settings.get('without_proxy', False))}", 
                callback_data="toggle_without_proxy"
            )],
            [InlineKeyboardButton(
                text=f"Работа без аккаунтов: {_on_off(settings.get('without_accounts', False))}", 
                callback_data="toggle_without_accounts"
            )],
            [InlineKeyboardButton(
                text=f"Ротация текстов: {_on_off(settings.get('text_rotation', False))}",
                callback_data="toggle_text_rotation"
            )],
            [InlineKeyboardButton(text="🔙 В настройки", callback_data="settings_back_root")],
        ]
    )

def get_autostart_menu(settings: dict) -> InlineKeyboardMarkup:
    timer = settings.get("autostart_timer")
    timer_text = f"{timer} сек." if timer else "Отключен"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"Текущее: {timer_text}", callback_data="noop")],
            [
                InlineKeyboardButton(text="5 мин", callback_data="set_autostart_preset:300"),
                InlineKeyboardButton(text="10 мин", callback_data="set_autostart_preset:600"),
                InlineKeyboardButton(text="15 мин", callback_data="set_autostart_preset:900"),
            ],
            [
                InlineKeyboardButton(text="30 мин", callback_data="set_autostart_preset:1800"),
                InlineKeyboardButton(text="45 мин", callback_data="set_autostart_preset:2700"),
                InlineKeyboardButton(text="60 мин", callback_data="set_autostart_preset:3600"),
            ],
            [InlineKeyboardButton(text="❌ Отключить", callback_data="set_autostart_preset:0")],
            [InlineKeyboardButton(text="✍️ Ввести вручную", callback_data="set_autostart_timer")],
            [InlineKeyboardButton(text="🔙 В настройки", callback_data="settings_back_root")],
        ]
    )

def get_fingerprint_menu(settings: dict) -> InlineKeyboardMarkup:
    ua_source = settings.get("ua_source", "random")
    ua_count = int(settings.get("ua_count", 0))
    random_res = settings.get("random_resolution", True)
    screen_res = settings.get("screen_resolution")
    hw_src = settings.get("hw_source", "auto")
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🧩 USER AGENT", callback_data="noop")],
            [
                InlineKeyboardButton(
                    text=f"Источник: {'📁 Файл' if ua_source == 'file' else '🎲 Рандом'}", 
                    callback_data="toggle_ua_source"
                ),
                InlineKeyboardButton(
                    text=f"Загрузить .txt (сейчас: {ua_count})", 
                    callback_data="upload_ua_file"
                ),
            ],
            [InlineKeyboardButton(text="🖥 РАЗРЕШЕНИЕ ЭКРАНА", callback_data="noop")],
            [
                InlineKeyboardButton(
                    text=f"Рандомное: {_on_off(random_res)}", 
                    callback_data="toggle_random_resolution"
                ),
                InlineKeyboardButton(
                    text=f"Выбор: {screen_res if (screen_res and not random_res) else '🎲 Рандом'}", 
                    callback_data="open_resolution_menu"
                ),
            ],
            [InlineKeyboardButton(text="🧠 УСТРОЙСТВО", callback_data="noop")],
            [InlineKeyboardButton(
                text=f"Настройки: {'🧠 Авто' if hw_src=='auto' else '✍️ Кастом'}", 
                callback_data="open_hardware_settings"
            )],
            [InlineKeyboardButton(text="🔙 В настройки", callback_data="settings_back_root")],
        ]
    )

def get_hardware_menu(settings: dict) -> InlineKeyboardMarkup:
    src = settings.get("hw_source", "auto")  # auto | custom
    vendor = settings.get("hw_gpu_vendor", "auto")
    model = settings.get("hw_gpu_model", "auto")
    noise = settings.get("hw_noise_level", "medium")  # low|medium|high
    hc = settings.get("hw_hc") or "auto"
    mem = settings.get("hw_mem") or "auto"
    plat = settings.get("hw_platform_override", "auto")  # auto|Win32|MacIntel
    mtp = settings.get("hw_max_touch_points", 0)
    cdepth = settings.get("hw_color_depth", 24)

    # Преобразуем значения для отображения
    noise_display = {"low": "Низкий", "medium": "Средний", "high": "Высокий"}.get(noise, noise)
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"Источник профиля: {'🧠 Авто' if src=='auto' else '✍️ Кастом'}", 
                callback_data="toggle_hw_source"
            )],
            [
                InlineKeyboardButton(text=f"GPU вендор: {vendor}", callback_data="cycle_hw_gpu_vendor"),
                InlineKeyboardButton(text=f"Модель: {model[:12]+'...' if len(str(model)) > 12 else model}", callback_data="cycle_hw_gpu_model"),
            ],
            [
                InlineKeyboardButton(text=f"Шум: {noise_display}", callback_data="cycle_hw_noise"),
                InlineKeyboardButton(text=f"CPU: {hc} потоков", callback_data="cycle_hw_hc"),
            ],
            [
                InlineKeyboardButton(text=f"RAM: {mem} GB", callback_data="cycle_hw_mem"),
                InlineKeyboardButton(text=f"OS: {plat}", callback_data="cycle_hw_platform"),
            ],
            [
                InlineKeyboardButton(text=f"TouchPoints: {mtp}", callback_data="toggle_hw_mtp"),
                InlineKeyboardButton(text=f"ColorDepth: {cdepth}", callback_data="cycle_hw_cdepth"),
            ],
            [InlineKeyboardButton(text="🔙 В антидетект", callback_data="back_to_fingerprint")],
        ]
    )

def get_resolution_menu(current: str | None, random_enabled: bool = True) -> InlineKeyboardMarkup:
    """Меню выбора разрешения экрана"""
    presets = [
        "2560x1440",  # 2K
        "1920x1200",  # WUXGA
        "1920x1080",  # Full HD
        "1680x1050",  # WSXGA+
        "1600x900",   # HD+
        "1440x900"    # WXGA+
    ]
    
    rows = []
    
    # Кнопка рандома
    random_mark = "✅ " if random_enabled else ""
    rows.append([InlineKeyboardButton(
        text=f"{random_mark}🎲 Рандом из пресетов ПК", 
        callback_data="set_resolution:random"
    )])
    
    # Пресеты по 2 в ряду
    row = []
    for idx, res in enumerate(presets, start=1):
        mark = "✅ " if (current == res and not random_enabled) else ""
        row.append(InlineKeyboardButton(
            text=f"{mark}{res}", 
            callback_data=f"set_resolution:{res}"
        ))
        if idx % 2 == 0:
            rows.append(row)
            row = []
    
    # Добавляем оставшийся элемент если есть
    if row:
        rows.append(row)
    
    # Кастомное разрешение
    rows.append([InlineKeyboardButton(
        text="✍️ Ввести своё (ШxВ)", 
        callback_data="enter_custom_resolution"
    )])
    
    # Кнопка назад
    rows.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_fingerprint")])
    
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_back_menu() -> InlineKeyboardMarkup:
    """Простое меню с кнопкой назад"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
        ]
    )

# ============= НОВЫЕ ФУНКЦИИ ДЛЯ API =============

def get_api_main_menu(is_configured: bool) -> InlineKeyboardMarkup:
    """Главное меню настроек API"""
    kb = [
        [InlineKeyboardButton(text="🔑 Токены Bastart", callback_data="api_tokens_menu")],
        [InlineKeyboardButton(text="⚙️ Настройки сервиса", callback_data="api_service_menu")],
        [InlineKeyboardButton(text="🌐 URL адреса", callback_data="api_urls_menu")],
    ]
    
    if is_configured:
        kb.append([InlineKeyboardButton(text="🧪 Тест API", callback_data="api_test")])
    
    kb.append([InlineKeyboardButton(text="🔙 В настройки", callback_data="settings_back_root")])
    
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_api_settings_menu() -> InlineKeyboardMarkup:
    """Меню настроек API (используется в обработчике open_api_settings)"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌍 Выбрать страну/сервис", callback_data="api_selector_settings")],
            [InlineKeyboardButton(text="🧪 Тест API", callback_data="test_api_settings")],
            [InlineKeyboardButton(text="📋 Перейти к площадкам", callback_data="work_platforms")],
            [InlineKeyboardButton(text="🔙 В настройки", callback_data="settings_back_root")]
        ]
    )

def get_api_error_menu() -> InlineKeyboardMarkup:
    """Меню при ошибке API"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 К площадкам", callback_data="work_platforms")],
            [InlineKeyboardButton(text="🔙 В настройки", callback_data="settings_back_root")]
        ]
    )