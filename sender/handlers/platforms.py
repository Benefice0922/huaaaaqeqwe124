from aiogram import Router, F, types
from aiogram.enums import ContentType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from keyboards.platforms import get_countries_menu, get_platforms_menu, get_platform_settings_menu
from db import get_platform_settings, set_platform_setting, get_cookie_accounts
import html

router = Router()
router.event_types = {"message", "callback_query"}

# --- FSM ---
class PlatformSettings(StatesGroup):
    waiting_for_value = State()

# --- Настройки ---
SETTINGS_LABELS = {
    "custom_text": "Кастомный текст",
    "max_unsubscribes": "Лимит отписок",
    "max_proxies_per_account": "Лимит прокси",
    "browser_count": "Количество браузеров",
    "categories": "Категории",
    "selectors": "Доп. селекторы",
    "multithread": "Мультипоток"
}

PARSING_SELECTORS = [
    "Парс имени",
    "Парс цены",
    "Парс названия"
]

SELECTOR_TO_TAG = {
    "Парс имени": "[Name]",
    "Парс цены": "[Price]",
    "Парс названия": "[Title]"
}

async def safe_edit_text(callback, text, reply_markup=None, parse_mode=None):
    try:
        if (hasattr(callback.message, 'text') and callback.message.text == text and
            hasattr(callback.message, 'reply_markup') and callback.message.reply_markup == reply_markup):
            return
        await callback.message.edit_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
    except Exception as e:
        print(f"[EDIT ERROR] {e}")

@router.callback_query(F.data == "work_platforms")
async def platforms_menu(callback: types.CallbackQuery):
    await safe_edit_text(
        callback,
        "<b>Выберите страну:</b>",
        reply_markup=get_countries_menu(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "country_kz")
async def kz_platforms_menu(callback: types.CallbackQuery):
    await safe_edit_text(
        callback,
        "<b>Площадки Казахстана:</b>\n\nВыберите нужную площадку:",
        reply_markup=get_platforms_menu("kz"),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "country_kg")
async def kg_platforms_menu(callback: types.CallbackQuery):
    await safe_edit_text(
        callback,
        "<b>Площадки Киргизии:</b>\n\nВыберите нужную площадку:",
        reply_markup=get_platforms_menu("kg"),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("edit_selectors_back_"))
async def back_to_settings_from_selectors(callback: types.CallbackQuery):
    data_parts = callback.data.split("_")
    if len(data_parts) < 4:
        await callback.answer("❌ Ошибка данных.")
        return
    platform = data_parts[-1]
    settings = get_platform_settings(platform)
    config_text = format_settings_text(settings)
    domain = "kg" if platform == "lalafo" else "kz"
    platform_title = f"{platform.capitalize()}.{domain}"
    try:
        await callback.message.edit_text(
            text=f"<b>{platform_title}</b>\n\n{config_text}\n\n🔧 <b>Настройки площадки:</b>",
            reply_markup=get_platform_settings_menu(platform, settings),
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"[BACK TO SETTINGS ERROR] {e}")
    await callback.answer("🔙 Возврат к настройкам.")

@router.callback_query(F.data == "back_to_countries")
async def back_to_countries(callback: types.CallbackQuery):
    await platforms_menu(callback)

@router.callback_query(F.data == "krisha")
async def krisha_selected(callback: types.CallbackQuery):
    settings = get_platform_settings("krisha")
    await callback.answer()
    config_text = format_settings_text(settings)
    await safe_edit_text(
        callback,
        f"<b>Krisha.kz</b>\n\n{config_text}\n\n🔧 <b>Настройки площадки:</b>",
        reply_markup=get_platform_settings_menu("krisha", settings),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "kolesa")
async def kolesa_selected(callback: types.CallbackQuery):
    settings = get_platform_settings("kolesa")
    await callback.answer()
    config_text = format_settings_text(settings)
    await safe_edit_text(
        callback,
        f"<b>Kolesa.kz</b>\n\n{config_text}\n\n🔧 <b>Настройки площадки:</b>",
        reply_markup=get_platform_settings_menu("kolesa", settings),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "lalafo")
async def lalafo_selected(callback: types.CallbackQuery):
    settings = get_platform_settings("lalafo")
    cookie_accounts = get_cookie_accounts()
    cookie_count = len(cookie_accounts)
    await callback.answer()
    config_text = format_settings_text(settings)
    config_text += f"\n\n🍪 <b>Доступно cookie-аккаунтов:</b> <code>{cookie_count}</code>"
    await safe_edit_text(
        callback,
        f"<b>Lalafo.kg</b>\n\n{config_text}\n\n🔧 <b>Настройки площадки:</b>",
        reply_markup=get_platform_settings_menu("lalafo", settings),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "platforms")
async def back_to_platforms_by_country(callback: types.CallbackQuery, state: FSMContext = None):
    text = callback.message.text or ""
    country = "kz"
    if "Lalafo" in text or "lalafo" in text:
        country = "kg"
    if state:
        data = await state.get_data()
        platform = data.get("platform")
        if platform == "lalafo":
            country = "kg"
    if country == "kg":
        await kg_platforms_menu(callback)
    else:
        await kz_platforms_menu(callback)

@router.callback_query(F.data == "back_to_main")
async def platforms_back(callback: types.CallbackQuery):
    await callback.answer()
    try:
        from handlers.main_menu import cmd_start
        await cmd_start(callback.message)
    except Exception as e:
        print(f"[BACK TO MAIN ERROR] {e}")
        await callback.message.edit_text(
            "Главное меню",
            parse_mode="HTML"
        )

def format_settings_text(settings: dict) -> str:
    text = ""
    custom_text = settings.get("custom_text", "Не задано")
    # Кастомный текст: строка или список
    if isinstance(custom_text, list):
        text += f"📝 <b>Кастомный текст:</b> <i>{len(custom_text)} вариантов</i>\n"
        if custom_text:
            preview = html.escape(custom_text[0])
            text += f"<pre>{preview}</pre>\n"
    elif isinstance(custom_text, str) and custom_text != "Не задано":
        safe_text = html.escape(custom_text)
        if len(safe_text) > 300:
            safe_text = safe_text[:300] + "..."
        text += f"📝 <b>Кастомный текст:</b>\n<pre>{safe_text}</pre>\n"
    else:
        text += f"📝 <b>Кастомный текст:</b> <i>Не задано</i>\n"

    unsub = settings.get("max_unsubscribes", "—")
    proxy = settings.get("max_proxies_per_account", "—")
    text += f"📤 <b>Лимит отписок:</b> <code>{unsub}</code> | 🌐 <b>Лимит прокси:</b> <code>{proxy}</code>\n"

    browsers = settings.get("browser_count", "—")
    text += f"🖥️ <b>Количество браузеров:</b> <code>{browsers}</code>\n"

    categories = settings.get("categories", [])
    if isinstance(categories, list):
        cats_str = "\n".join(categories) if categories else "—"
    else:
        cats_str = str(categories)
    text += f"🏷️ <b>Категории:</b>\n<code>{cats_str}</code>\n"

    selectors = settings.get("selectors", [])
    if not isinstance(selectors, list):
        selectors = [str(selectors)] if selectors else []
    sel_tags = [SELECTOR_TO_TAG.get(sel, sel) for sel in selectors]
    sel_str = ", ".join(sel_tags) if sel_tags else "—"
    text += f"🔎 <b>Доп. селекторы:</b> <code>{sel_str}</code>\n"

    mt = "✅ Включен" if settings.get("multithread", False) else "❌ Отключен"
    text += f"🔄 <b>Мультипоток:</b> {mt}"

    return text.strip()

@router.callback_query(F.data.startswith("edit_"))
async def edit_setting(callback: types.CallbackQuery, state: FSMContext):
    if callback.data.startswith("edit_selectors_back_"):
        return
    parts = callback.data.split("_")
    if len(parts) < 3:
        await callback.answer("❌ Ошибка: неверные данные")
        return
    key = "_".join(parts[1:-1])
    platform = parts[-1]
    if key not in SETTINGS_LABELS:
        await callback.answer("❌ Неизвестная настройка")
        return
    await state.update_data(editing_key=key, platform=platform)
    if key == "selectors":
        await show_selectors_menu(callback, platform)
        return
    if key == "categories":
        await callback.message.edit_text(
            f"🔧 <b>Редактирование: {SETTINGS_LABELS[key]}</b>\n\n"
            "Вставьте список ссылок категорий, каждая с новой строки:",
            parse_mode="HTML",
            reply_markup=None
        )
    elif key == "custom_text":
        await callback.message.edit_text(
            f"🔧 <b>Редактирование: {SETTINGS_LABELS[key]}</b>\n\n"
            "Пришлите .txt файл с вариантами (разделитель — восемь дефисов --------), "
            "или отправьте текст вручную.",
            parse_mode="HTML",
            reply_markup=None
        )
    else:
        await callback.message.edit_text(
            f"🔧 <b>Редактирование: {SETTINGS_LABELS[key]}</b>\n\n"
            "Введите новое значение:",
            parse_mode="HTML",
            reply_markup=None
        )
    await state.set_state(PlatformSettings.waiting_for_value)
    await callback.answer()

@router.message(PlatformSettings.waiting_for_value, F.content_type.in_({ContentType.TEXT, ContentType.DOCUMENT}))
async def save_setting_value(message: types.Message, state: FSMContext):
    data = await state.get_data()
    key = data.get("editing_key")
    platform = data.get("platform")

    if not key or not platform:
        await message.answer("❌ Сессия редактирования утеряна. Попробуйте снова.")
        await state.clear()
        return

    # 1) Кастомный текст
    if key == "custom_text":
        if message.content_type == ContentType.DOCUMENT and message.document:
            doc = message.document
            if not doc.file_name.lower().endswith(".txt"):
                await message.answer("Нужен .txt файл.")
                return
            try:
                buf = await message.bot.download(doc)
                content = buf.read().decode("utf-8", errors="ignore")
                texts = [t.strip() for t in content.split("--------") if t.strip()]
                set_platform_setting(platform, key, texts)
                await message.answer(f"✅ Загружено вариантов кастомного текста: {len(texts)}")
            except Exception as e:
                print(f"[CUSTOM_TEXT FILE ERROR] {e}")
                await message.answer(f"Ошибка загрузки файла: {e}")
                return
        else:
            user_input = (message.text or "").strip()
            if not user_input:
                await message.answer("❌ Значение не может быть пустым.")
                return
            set_platform_setting(platform, key, user_input)
            await message.answer("✅ Настройка обновлена.")
    else:
        # 2) Прочие настройки
        if message.content_type != ContentType.TEXT:
            await message.answer("❌ Ожидался текст. Пожалуйста, отправьте значение сообщением.")
            return

        user_input = (message.text or "").strip()
        if not user_input:
            await message.answer("❌ Значение не может быть пустым.")
            return

        if key in ["max_unsubscribes", "max_proxies_per_account", "browser_count"]:
            try:
                user_input = int(user_input)
            except ValueError:
                await message.answer("❌ Ожидалось число. Попробуйте снова:")
                return
        elif key == "categories":
            raw_lines = [line for line in user_input.splitlines() if line.strip()]
            categories = []
            for line in raw_lines:
                parts = [p.strip() for p in line.split(",") if p.strip()]
                categories.extend(parts)
            user_input = categories

        set_platform_setting(platform, key, user_input)
        await message.answer("✅ Настройка обновлена.")

    # Вернёмся к меню настроек площадки
    settings = get_platform_settings(platform)
    config_text = format_settings_text(settings)
    domain = "kg" if platform == "lalafo" else "kz"
    platform_title = f"{platform.capitalize()}.{domain}"
    if platform == "lalafo":
        cookie_accounts = get_cookie_accounts()
        cookie_count = len(cookie_accounts)
        config_text += f"\n\n🍪 <b>Доступно cookie-аккаунтов:</b> <code>{cookie_count}</code>"
    await message.answer(
        f"<b>{platform_title}</b>\n\n{config_text}\n\n🔧 <b>Настройки площадки:</b>",
        reply_markup=get_platform_settings_menu(platform, settings),
        parse_mode="HTML"
    )
    await state.clear()

async def show_selectors_menu(callback: types.CallbackQuery, platform: str):
    settings = get_platform_settings(platform)
    saved_selectors = settings.get("selectors", [])
    if not isinstance(saved_selectors, list):
        saved_selectors = []
    kb = []
    for selector in PARSING_SELECTORS:
        status = "✅" if selector in saved_selectors else "❌"
        callback_data = f"toggle_selector_{selector.replace(' ', '_')}_{platform}"
        kb.append([
            types.InlineKeyboardButton(
                text=f"{status} {selector}",
                callback_data=callback_data
            )
        ])
    kb.append([
        types.InlineKeyboardButton(
            text="🔙 Назад",
            callback_data=f"edit_selectors_back_{platform}"
        )
    ])
    try:
        await callback.message.edit_text(
            text="Выберите селекторы для парсинга:",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb)
        )
    except Exception as e:
        print(f"[SELECTORS MENU ERROR] {e}")
    await callback.answer()

@router.callback_query(F.data.startswith("toggle_selector_"))
async def toggle_selector(callback: types.CallbackQuery):
    data_parts = callback.data.split("_")
    if len(data_parts) < 4:
        await callback.answer("❌ Ошибка данных селектора.")
        return
    platform = data_parts[-1]
    selector_key = "_".join(data_parts[2:-1])
    selector = selector_key.replace("_", " ")
    settings = get_platform_settings(platform)
    saved_selectors = settings.get("selectors", [])
    if not isinstance(saved_selectors, list):
        saved_selectors = []
    if selector in saved_selectors:
        saved_selectors.remove(selector)
        action_text = f"❌ Селектор '{selector}' выключен."
    else:
        saved_selectors.append(selector)
        action_text = f"✅ Селектор '{selector}' включен."
    set_platform_setting(platform, "selectors", saved_selectors)
    await show_selectors_menu(callback, platform)
    await callback.answer(action_text)

@router.callback_query(F.data.startswith("toggle_multithread_"))
async def toggle_multithread_callback(callback: types.CallbackQuery):
    platform = callback.data.split("_")[2]
    settings = get_platform_settings(platform)
    new_value = not settings.get('multithread', False)
    set_platform_setting(platform, 'multithread', new_value)
    action_text = f"Мультипоток {'включён' if new_value else 'отключён'} для {platform.capitalize()}"
    await callback.answer(action_text)
    settings = get_platform_settings(platform)
    config_text = format_settings_text(settings)
    domain = "kg" if platform == "lalafo" else "kz"
    platform_title = f"{platform.capitalize()}.{domain}"
    if platform == "lalafo":
        cookie_accounts = get_cookie_accounts()
        cookie_count = len(cookie_accounts)
        config_text += f"\n\n🍪 <b>Доступно cookie-аккаунтов:</b> <code>{cookie_count}</code>"
    try:
        await callback.message.edit_text(
            text=f"<b>{platform_title}</b>\n\n{config_text}\n\n🔧 <b>Настройки площадки:</b>",
            reply_markup=get_platform_settings_menu(platform, settings),
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"[MULTITHREAD TOGGLE ERROR] {e}")