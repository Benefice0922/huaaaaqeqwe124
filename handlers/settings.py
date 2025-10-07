from __future__ import annotations

import io
import re
import os
import json
import aiohttp
from typing import List

from aiogram import Router, F, types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db import get_settings, set_setting
from keyboards.settings import (
    get_settings_menu,
    get_common_menu,
    get_autostart_menu,
    get_fingerprint_menu,
    get_resolution_menu,
    get_hardware_menu,
    get_back_menu,
    get_api_main_menu,  # Добавим эту функцию в keyboards/settings.py
)

router = Router()
router.event_types = {"message", "callback_query"}
API_CATALOG_CACHE = {}
class SettingsFSM(StatesGroup):
    waiting_for_timer = State()
    waiting_for_ua_file = State()
    waiting_for_custom_resolution = State()
    # Новые состояния для API
    waiting_for_bastart_project_token = State()
    waiting_for_bastart_worker_token = State()
    waiting_for_api_url = State()
    waiting_for_shortener_url = State()
    waiting_for_platform_id = State()
    waiting_for_profile_id = State()
    waiting_for_price = State()

def build_root_caption(s: dict) -> str:
    visible = "👁️ Видим" if s.get("browser_visible") else "🙈 Скрыт"
    no_proxy = "✅" if s.get("without_proxy") else "❌"
    no_acc = "✅" if s.get("without_accounts") else "❌"
    timer = s.get("autostart_timer")
    timer_txt = f"{timer} сек." if timer else "Отключен"
    ua_source = s.get("ua_source", "random")
    ua_count = int(s.get("ua_count", 0))
    ua_txt = "🎲 Рандом" if ua_source != "file" else f"📁 Файл ({ua_count})"
    res_txt = s.get("screen_resolution") if (s.get("screen_resolution") and not s.get("random_resolution", True)) else "🎲 Рандом (ПК ≥1440×900)"
    hw_src = s.get("hw_source", "auto")
    
    # Добавляем информацию об API
    api_status = "❌ Не настроен"
    try:
        if os.path.exists('settings.json'):
            with open('settings.json', 'r', encoding='utf-8') as f:
                settings_data = json.load(f)
                api_settings = settings_data.get("api_settings", {})
                if api_settings.get("bastart_project_token") and api_settings.get("bastart_worker_token"):
                    platform_id = api_settings.get("default_platform_id", "?")
                    api_status = f"✅ Platform: {platform_id}"
    except:
        pass
    
    return (
        "⚙️ <b>Настройки</b>\n\n"
        "🕵️ <b>Антидетект</b>\n"
        f"• UA: <code>{ua_txt}</code>\n"
        f"• Разрешение: <code>{res_txt}</code>\n"
        f"• Устройство: <code>{'Авто' if hw_src=='auto' else 'Кастом'}</code>\n\n"
        "⚙️ <b>Общие</b>\n"
        f"• Видимость браузера: <code>{visible}</code>\n"
        f"• Без прокси: <code>{no_proxy}</code> | Без аккаунтов: <code>{no_acc}</code>\n\n"
        "🔗 <b>API для ссылок</b>\n"
        f"• Статус: <code>{api_status}</code>\n\n"
        "⏱ <b>Автозапуск</b>\n"
        f"• Таймер: <code>{timer_txt}</code>"
    )

def build_autostart_caption(s: dict) -> str:
    t = s.get("autostart_timer")
    ttxt = f"{t} сек." if t else "Отключен"
    return "⏱ <b>Автозапуск</b>\nТекущее значение: <code>{}</code>\n\nВыберите пресет или введите своё значение в секундах.".format(ttxt)

def build_fingerprint_caption(s: dict) -> str:
    ua_source = s.get("ua_source", "random")
    ua_count = int(s.get("ua_count", 0))
    ua_txt = "🎲 Рандом" if ua_source != "file" else f"📁 Файл ({ua_count})"
    res_txt = s.get("screen_resolution") if (s.get("screen_resolution") and not s.get("random_resolution", True)) else "🎲 Рандом (ПК ≥1440×900)"
    hw_src = s.get("hw_source", "auto")
    return (
        "🕵️ <b>Антидетект</b>\n"
        f"• Источник UA: <code>{ua_txt}</code>\n"
        f"• Разрешение: <code>{res_txt}</code>\n"
        f"• Устройство: <code>{'Авто' if hw_src=='auto' else 'Кастом'}</code>\n\n"
        "Загрузите файл UA / переключите источник, настройте разрешение и устройство."
    )

# Вспомогательные функции для API
def save_api_setting(key: str, value):
    """Сохранить настройку API"""
    settings = {}
    if os.path.exists('settings.json'):
        with open('settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
    
    if "api_settings" not in settings:
        settings["api_settings"] = {}
    
    settings["api_settings"][key] = value
    
    with open('settings.json', 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

def get_api_settings():
    """Получить настройки API"""
    if os.path.exists('settings.json'):
        with open('settings.json', 'r', encoding='utf-8') as f:
            settings = json.load(f)
            return settings.get("api_settings", {})
    return {}

@router.callback_query(F.data == "settings")
async def show_settings(callback: types.CallbackQuery):
    s = get_settings()
    await callback.answer()
    await callback.message.edit_text(build_root_caption(s), reply_markup=get_settings_menu(s), parse_mode="HTML")

@router.callback_query(F.data == "settings_back_root")
async def settings_back_root(callback: types.CallbackQuery):
    s = get_settings()
    await callback.answer()
    await callback.message.edit_text(build_root_caption(s), reply_markup=get_settings_menu(s), parse_mode="HTML")

@router.callback_query(F.data == "open_common_settings")
async def open_common_settings(callback: types.CallbackQuery):
    await callback.answer()
    s = get_settings()
    await callback.message.edit_text("⚙️ <b>Общие настройки</b>\nВыберите, что включить/выключить:", reply_markup=get_common_menu(s), parse_mode="HTML")

# ============= НАСТРОЙКИ API =============

@router.callback_query(F.data == "open_api_settings")
async def open_api_settings(callback: types.CallbackQuery):
    """Открыть главное меню настроек API"""
    await callback.answer()
    
    try:
        # Загружаем текущие настройки
        api_settings = get_api_settings()
        
        # Проверяем настройки
        is_configured = bool(
            api_settings.get("bastart_project_token") and 
            api_settings.get("bastart_worker_token")
        )
        
        # Получаем текущие значения
        project_token = api_settings.get("bastart_project_token", "")
        worker_token = api_settings.get("bastart_worker_token", "")
        api_url = api_settings.get("bastart_api_url", "https://web-api.bdev.su/")
        shortener_url = api_settings.get("shortener_api_url", "http://193.233.112.8/api/shorten")
        platform_id = api_settings.get("default_platform_id", 1)
        profile_id = api_settings.get("default_profile_id", 379783)
        price = api_settings.get("default_price", 0.11)
        
        # Статус
        status_emoji = "✅" if is_configured else "❌"
        status_text = "Настроен" if is_configured else "Не настроен"
        
        # Формируем текст
        text = (
            f"🔗 <b>Настройки API для ссылок</b>\n\n"
            f"<b>Статус:</b> {status_emoji} {status_text}\n\n"
            f"<b>🔑 Токены Bastart:</b>\n"
        )
        
        if project_token:
            text += f"• Project: <code>{project_token[:15]}...</code>\n"
        else:
            text += "• Project: <code>не задан</code>\n"
            
        if worker_token:
            text += f"• Worker: <code>{worker_token[:15]}...</code>\n\n"
        else:
            text += "• Worker: <code>не задан</code>\n\n"
            
        text += (
            f"<b>📡 Сервис:</b>\n"
            f"• Platform ID: <code>{platform_id}</code>\n"
            f"• Profile ID: <code>{profile_id}</code>\n"
            f"• Цена: <code>{price}</code>\n\n"
            f"<b>🌐 URL-адреса:</b>\n"
            f"• API: <code>{api_url}</code>\n"
            f"• Shortener: <code>{shortener_url}</code>"
        )
        
        # Создаем клавиатуру
        kb = get_api_main_menu(is_configured)
        
        await callback.message.edit_text(
            text,
            reply_markup=kb,
            parse_mode="HTML"
        )
        
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка: {str(e)}",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="🔙 Назад", callback_data="settings_back_root")]
            ]),
            parse_mode="HTML"
        )

# Меню настройки токенов
@router.callback_query(F.data == "api_tokens_menu")
async def api_tokens_menu(callback: types.CallbackQuery):
    """Меню настройки токенов Bastart"""
    await callback.answer()
    
    api_settings = get_api_settings()
    project_token = api_settings.get("bastart_project_token", "")
    worker_token = api_settings.get("bastart_worker_token", "")
    
    text = (
        "🔑 <b>Токены Bastart API</b>\n\n"
        f"<b>Project Token:</b>\n<code>{project_token if project_token else 'не задан'}</code>\n\n"
        f"<b>Worker Token:</b>\n<code>{worker_token if worker_token else 'не задан'}</code>\n\n"
        "Выберите токен для изменения:"
    )
    
    kb = [
        [types.InlineKeyboardButton(text="📝 Project Token", callback_data="set_project_token")],
        [types.InlineKeyboardButton(text="📝 Worker Token", callback_data="set_worker_token")],
        [types.InlineKeyboardButton(text="🔙 Назад", callback_data="open_api_settings")]
    ]
    
    await callback.message.edit_text(
        text,
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode="HTML"
    )

# Меню настройки сервиса
# Заменяем функцию api_service_menu на новую версию с кнопками выбора

@router.callback_query(F.data == "api_profiles_select")
async def api_profiles_select(callback: types.CallbackQuery):
    """Показать список профилей для выбора"""
    print(f"[DEBUG] api_profiles_select called by user {callback.from_user.id}")
    await callback.answer("🔄 Загрузка профилей...")
    
    api_settings = get_api_settings()
    print(f"[DEBUG] API settings loaded: {bool(api_settings)}")
    
    project_token = api_settings.get("bastart_project_token", "")
    worker_token = api_settings.get("bastart_worker_token", "")
    api_url = api_settings.get("bastart_api_url", "https://web-api.bdev.su/")
    
    print(f"[DEBUG] Tokens: project={bool(project_token)}, worker={bool(worker_token)}")
    
    if not project_token or not worker_token:
        print("[DEBUG] Tokens not configured")
        await callback.message.edit_text(
            "❌ <b>Ошибка:</b> Сначала настройте токены!",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="🔑 Настроить токены", callback_data="api_tokens_menu")],
                [types.InlineKeyboardButton(text="🔙 Назад", callback_data="api_service_menu")]
            ]),
            parse_mode="HTML"
        )
        return
    
    # Используем глобальный кэш вместо bot.storage
    user_id = callback.from_user.id
    catalog = API_CATALOG_CACHE.get(user_id)
    
    print(f"[DEBUG] Catalog from cache: {bool(catalog)}")
    
    if not catalog:
        print("[DEBUG] Loading catalog from API...")
        # GET запрос к API
        headers = {
            "X-Team-Token": project_token,
            "X-User-Token": worker_token,
            "Accept": "application/json"
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                print(f"[DEBUG] Making GET request to {api_url}")
                async with session.get(api_url, headers=headers) as resp:
                    print(f"[DEBUG] Response status: {resp.status}")
                    if resp.status == 200:
                        catalog = await resp.json()
                        print(f"[DEBUG] Catalog loaded, keys: {catalog.keys() if catalog else 'None'}")
                        # Сохраняем каталог в глобальный кэш
                        API_CATALOG_CACHE[user_id] = catalog
                    else:
                        error_text = await resp.text()
                        print(f"[DEBUG] API Error: {error_text}")
                        await callback.answer(f"Ошибка API: {resp.status}", show_alert=True)
                        return
        except Exception as e:
            print(f"[DEBUG] Exception during API call: {str(e)}")
            await callback.answer(f"Ошибка: {str(e)}", show_alert=True)
            return
    
    # Показываем профили
    if catalog and "your_profiles" in catalog:
        profiles = catalog["your_profiles"]
        print(f"[DEBUG] Profiles count: {len(profiles)}")
        
        if not profiles:
            print("[DEBUG] No profiles available")
            await callback.message.edit_text(
                "❌ <b>Нет доступных профилей</b>\n\n"
                "Создайте профиль в Bastart API",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text="🔙 Назад", callback_data="api_service_menu")]
                ]),
                parse_mode="HTML"
            )
            return
        
        kb = []
        current_profile_id = api_settings.get("default_profile_id")
        
        for profile in profiles[:10]:  # Показываем первые 10
            profile_id = profile.get("id")
            profile_data = profile.get("data", {})
            
            # Формируем название профиля
            name = profile_data.get("name", "")
            fio = profile_data.get("fio", "")
            phone = profile_data.get("phone", "")
            
            # Приоритет: name -> fio -> phone
            display_name = name or fio or phone or f"Профиль #{profile_id}"
            
            # Добавляем дополнительную информацию
            display_text = f"#{profile_id}: {display_name}"
            if phone and display_name != phone:
                display_text += f" • {phone}"
            
            # Отмечаем текущий профиль
            if profile_id == current_profile_id:
                display_text = f"✅ {display_text}"
            
            kb.append([
                types.InlineKeyboardButton(
                    text=display_text[:64],  # Ограничение Telegram
                    callback_data=f"api_set_profile:{profile_id}"
                )
            ])
        
        if len(profiles) > 10:
            kb.append([
                types.InlineKeyboardButton(
                    text=f"Показано 10 из {len(profiles)} профилей",
                    callback_data="noop"
                )
            ])
        
        kb.append([
            types.InlineKeyboardButton(text="🔙 Назад", callback_data="api_service_menu")
        ])
        
        print(f"[DEBUG] Sending menu with {len(kb)} buttons")
        await callback.message.edit_text(
            "👤 <b>Выберите профиль:</b>\n\n"
            f"Всего профилей: {len(profiles)}",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb),
            parse_mode="HTML"
        )
    else:
        print(f"[DEBUG] Catalog structure issue. Has catalog: {bool(catalog)}, has your_profiles: {'your_profiles' in catalog if catalog else False}")
        await callback.answer("Нет данных о профилях", show_alert=True)

# Обновленный обработчик установки профиля
@router.callback_query(F.data.startswith("api_set_profile:"))
async def api_set_profile(callback: types.CallbackQuery):
    """Установить выбранный Profile ID"""
    profile_id = int(callback.data.split(":", 1)[1])
    
    # Сохраняем в настройки
    save_api_setting("default_profile_id", profile_id)
    
    # Получаем информацию о профиле из кэша
    profile_name = f"#{profile_id}"
    user_id = callback.from_user.id
    catalog = API_CATALOG_CACHE.get(user_id)
    
    if catalog and "your_profiles" in catalog:
        for profile in catalog["your_profiles"]:
            if profile.get("id") == profile_id:
                profile_data = profile.get("data", {})
                name = profile_data.get("name", "")
                fio = profile_data.get("fio", "")
                profile_name = name or fio or f"#{profile_id}"
                break
    
    await callback.answer(f"✅ Установлен профиль: {profile_name}", show_alert=True)
    await api_service_menu(callback)

# Обновленный обработчик выбора каталога
@router.callback_query(F.data == "api_catalog_select")
async def api_catalog_select(callback: types.CallbackQuery):
    """Загрузить каталог и показать страны"""
    print(f"[DEBUG] api_catalog_select called by user {callback.from_user.id}")
    await callback.answer("🔄 Загрузка каталога...")
    
    api_settings = get_api_settings()
    project_token = api_settings.get("bastart_project_token", "")
    worker_token = api_settings.get("bastart_worker_token", "")
    api_url = api_settings.get("bastart_api_url", "https://web-api.bdev.su/")
    
    print(f"[DEBUG] API URL: {api_url}")
    print(f"[DEBUG] Tokens present: project={bool(project_token)}, worker={bool(worker_token)}")
    
    if not project_token or not worker_token:
        await callback.message.edit_text(
            "❌ <b>Ошибка:</b> Сначала настройте токены!",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="🔑 Настроить токены", callback_data="api_tokens_menu")],
                [types.InlineKeyboardButton(text="🔙 Назад", callback_data="api_service_menu")]
            ]),
            parse_mode="HTML"
        )
        return
    
    # GET запрос к API
    headers = {
        "X-Team-Token": project_token,
        "X-User-Token": worker_token,
        "Accept": "application/json"
    }
    
    print(f"[DEBUG] Headers: {headers}")
    
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            print(f"[DEBUG] Making GET request...")
            async with session.get(api_url, headers=headers) as resp:
                print(f"[DEBUG] Response status: {resp.status}")
                if resp.status == 200:
                    catalog = await resp.json()
                    print(f"[DEBUG] Catalog keys: {catalog.keys() if catalog else 'None'}")
                    
                    # Сохраняем каталог в глобальный кэш
                    user_id = callback.from_user.id
                    API_CATALOG_CACHE[user_id] = catalog
                    
                    # Показываем страны
                    if catalog.get("sites_list"):
                        sites_list = catalog["sites_list"]
                        print(f"[DEBUG] Countries: {list(sites_list.keys())}")
                        
                        kb = []
                        for country in sorted(sites_list.keys()):
                            services_count = len(sites_list[country])
                            print(f"[DEBUG] Country: {country}, services: {services_count}")
                            kb.append([
                                types.InlineKeyboardButton(
                                    text=f"{country} ({services_count} сервисов)",
                                    callback_data=f"api_country:{country}"
                                )
                            ])
                        
                        kb.append([
                            types.InlineKeyboardButton(text="🔙 Назад", callback_data="api_service_menu")
                        ])
                        
                        print(f"[DEBUG] Sending menu with {len(kb)} buttons")
                        await callback.message.edit_text(
                            "🌍 <b>Выберите страну:</b>",
                            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb),
                            parse_mode="HTML"
                        )
                    else:
                        print("[DEBUG] sites_list is empty or missing")
                        await callback.answer("Каталог пуст", show_alert=True)
                else:
                    error_text = await resp.text()
                    print(f"[DEBUG] API Error response: {error_text}")
                    await callback.answer(f"Ошибка API: {resp.status}", show_alert=True)
                    
    except Exception as e:
        print(f"[DEBUG] Exception: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        await callback.answer(f"Ошибка: {str(e)}", show_alert=True)

# Обновленный обработчик выбора страны
@router.callback_query(F.data.startswith("api_country:"))
async def api_country_selected(callback: types.CallbackQuery):
    """Показать сервисы выбранной страны с эмодзи и группировкой"""
    country = callback.data.split(":", 1)[1]
    print(f"[DEBUG] api_country_selected: {country}")
    
    # Получаем каталог из глобального кэша
    user_id = callback.from_user.id
    catalog = API_CATALOG_CACHE.get(user_id)
    
    print(f"[DEBUG] Catalog from cache: {bool(catalog)}")
    
    if not catalog or "sites_list" not in catalog:
        print("[DEBUG] Catalog not loaded")
        await callback.answer("Каталог не загружен", show_alert=True)
        return
    
    services = catalog["sites_list"].get(country, [])
    print(f"[DEBUG] Services for {country}: {len(services)}")
    
    if not services:
        await callback.answer("Нет сервисов", show_alert=True)
        return
    
    # Группируем сервисы по типам
    verif_services = []
    delivery_services = []
    marketplace_services = []
    bank_services = []
    other_services = []
    
    for service in services:
        name = service.get("name", "").lower()
        service_obj = service
        
        if "verif" in name:
            verif_services.append(service_obj)
        elif any(x in name for x in ["доставка", "post", "почт", "сдек", "cdek", "dpd", "express", "cargo", "jet", "logistic"]):
            delivery_services.append(service_obj)
        elif any(x in name for x in ["bank", "банк", "pay", "western", "money", "korona", "halyk", "халык"]):
            bank_services.append(service_obj)
        elif any(x in name for x in ["olx", "krisha", "крыша", "kolesa", "lalafo", "wildberries", "ozon", "tap.az", "somon"]):
            marketplace_services.append(service_obj)
        else:
            other_services.append(service_obj)
    
    # Объединяем в порядке приоритета
    sorted_services = (
        verif_services + 
        marketplace_services + 
        delivery_services + 
        bank_services + 
        other_services
    )
    
    print(f"[DEBUG] Sorted services: {len(sorted_services)}")
    
    # Показываем сервисы с эмодзи
    kb = []
    api_settings = get_api_settings()
    current_platform_id = api_settings.get("default_platform_id")
    
    for service in sorted_services[:15]:  # Показываем первые 15
        service_id = service.get("id")
        service_name = service.get("name")
        
        # Добавляем эмодзи
        emoji = ""
        name_lower = service_name.lower()
        if "verif" in name_lower:
            emoji = "✅ "
        elif "olx" in name_lower or "lalafo" in name_lower or "tap.az" in name_lower:
            emoji = "📢 "
        elif "krisha" in name_lower or "крыша" in name_lower:
            emoji = "🏠 "
        elif "kolesa" in name_lower:
            emoji = "🚗 "
        elif any(x in name_lower for x in ["яндекс", "yandex"]):
            emoji = "📦 "
        elif any(x in name_lower for x in ["сдек", "cdek", "сдэк", "sdek"]):
            emoji = "📮 "
        elif any(x in name_lower for x in ["bank", "банк", "pay"]):
            emoji = "🏦 "
        elif "wildberries" in name_lower or "ozon" in name_lower:
            emoji = "🛍️ "
        elif "🆕" in service_name:
            emoji = "🆕 "
            service_name = service_name.replace("🆕", "").strip()
        
        # Отмечаем текущий сервис
        display_text = f"{emoji}{service_name}"
        if service_id == current_platform_id:
            display_text = f"✅ {display_text}"
        
        kb.append([
            types.InlineKeyboardButton(
                text=display_text,
                callback_data=f"api_set_service:{service_id}"
            )
        ])
    
    if len(sorted_services) > 15:
        kb.append([
            types.InlineKeyboardButton(
                text=f"Показано 15 из {len(sorted_services)} сервисов",
                callback_data="noop"
            )
        ])
    
    kb.append([
        types.InlineKeyboardButton(text="🔙 К странам", callback_data="api_catalog_select")
    ])
    
    # Добавляем флаг страны
    flags = {
        "Казахстан": "🇰🇿", "Узбекистан": "🇺🇿", "Киргизия": "🇰🇬",
        "Таджикистан": "🇹🇯", "Азербайджан": "🇦🇿", "Армения": "🇦🇲"
    }
    flag = flags.get(country, "🌍")
    
    print(f"[DEBUG] Sending menu with {len(kb)} buttons")
    await callback.message.edit_text(
        f"{flag} <b>{country}</b>\n"
        f"📋 Выберите сервис ({len(services)} доступно):",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode="HTML"
    )

# Обновленный обработчик меню сервиса
@router.callback_query(F.data == "api_service_menu")
async def api_service_menu(callback: types.CallbackQuery):
    """Меню настройки сервиса (Platform, Profile, Price)"""
    await callback.answer()
    
    api_settings = get_api_settings()
    platform_id = api_settings.get("default_platform_id", 1)
    profile_id = api_settings.get("default_profile_id", None)
    price = api_settings.get("default_price", 0.11)
    
    # Получаем название текущего сервиса
    service_name = "Не выбран"
    country_name = ""
    
    # Используем глобальный кэш
    user_id = callback.from_user.id
    catalog = API_CATALOG_CACHE.get(user_id)
    
    if catalog and "sites_list" in catalog:
        for country, services in catalog["sites_list"].items():
            for service in services:
                if service.get("id") == platform_id:
                    service_name = service.get("name", f"ID: {platform_id}")
                    country_name = country
                    break
            if service_name != "Не выбран":
                break
    
    # Получаем название профиля
    profile_name = "Не выбран"
    if profile_id and catalog and "your_profiles" in catalog:
        for profile in catalog["your_profiles"]:
            if profile.get("id") == profile_id:
                profile_data = profile.get("data", {})
                profile_name = profile_data.get("name") or profile_data.get("fio") or f"#{profile_id}"
                break
    
    text = (
        "⚙️ <b>Настройки сервиса</b>\n\n"
        f"<b>🌍 Сервис:</b> {service_name}"
    )
    if country_name:
        text += f" ({country_name})"
    text += f"\n<b>Platform ID:</b> <code>{platform_id}</code>\n\n"
    
    text += (
        f"<b>👤 Профиль:</b> {profile_name}\n"
        f"<b>Profile ID:</b> <code>{profile_id if profile_id else 'не выбран'}</code>\n\n"
        f"<b>💰 Цена:</b> <code>{price}</code>\n\n"
        "Выберите что настроить:"
    )
    
    kb = [
        [types.InlineKeyboardButton(text="🌍 Выбрать сервис", callback_data="api_catalog_select")],
        [types.InlineKeyboardButton(text="👤 Выбрать профиль", callback_data="api_profiles_select")],
        [types.InlineKeyboardButton(text="💰 Изменить цену", callback_data="set_api_price")],
        [types.InlineKeyboardButton(text="🔙 Назад", callback_data="open_api_settings")]
    ]
    
    await callback.message.edit_text(
        text,
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode="HTML"
    )
# Добавляем новый обработчик для выбора профилей

# Обработка выбора страны

# Установка выбранного сервиса
@router.callback_query(F.data.startswith("api_set_service:"))
async def api_set_service(callback: types.CallbackQuery):
    """Установить выбранный Platform ID"""
    platform_id = int(callback.data.split(":", 1)[1])
    
    # Сохраняем в настройки
    save_api_setting("default_platform_id", platform_id)
    
    await callback.answer(f"✅ Platform ID установлен: {platform_id}", show_alert=True)
    await api_service_menu(callback)

# Обработчики ввода токенов
@router.callback_query(F.data == "set_project_token")
async def set_project_token(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text(
        "🔑 Введите <b>Project Token</b> для Bastart API:",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="❌ Отмена", callback_data="api_tokens_menu")]
        ]),
        parse_mode="HTML"
    )
    await state.set_state(SettingsFSM.waiting_for_bastart_project_token)

@router.callback_query(F.data == "set_worker_token")
async def set_worker_token(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text(
        "🔑 Введите <b>Worker Token</b> для Bastart API:",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="❌ Отмена", callback_data="api_tokens_menu")]
        ]),
        parse_mode="HTML"
    )
    await state.set_state(SettingsFSM.waiting_for_bastart_worker_token)

@router.message(SettingsFSM.waiting_for_bastart_project_token, F.text)
async def receive_project_token(message: types.Message, state: FSMContext):
    token = message.text.strip()
    save_api_setting("bastart_project_token", token)
    await message.answer("✅ Project Token сохранен!")
    await state.clear()
    
    # Возвращаемся в меню токенов
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔙 К токенам", callback_data="api_tokens_menu")]
    ])
    await message.answer("Токен установлен", reply_markup=kb)

@router.message(SettingsFSM.waiting_for_bastart_worker_token, F.text)
async def receive_worker_token(message: types.Message, state: FSMContext):
    token = message.text.strip()
    save_api_setting("bastart_worker_token", token)
    await message.answer("✅ Worker Token сохранен!")
    await state.clear()
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔙 К токенам", callback_data="api_tokens_menu")]
    ])
    await message.answer("Токен установлен", reply_markup=kb)



# Меню настройки URL - ДОБАВЬТЕ ЭТОТ БЛОК
@router.callback_query(F.data == "api_urls_menu")
async def api_urls_menu(callback: types.CallbackQuery):
    """Меню настройки URL адресов"""
    await callback.answer()
    
    api_settings = get_api_settings()
    api_url = api_settings.get("bastart_api_url", "https://web-api.bdev.su/")
    shortener_url = api_settings.get("shortener_api_url", "http://193.233.112.8/api/shorten")
    
    text = (
        "🌐 <b>URL-адреса API</b>\n\n"
        f"<b>Bastart API:</b>\n<code>{api_url}</code>\n\n"
        f"<b>Shortener API:</b>\n<code>{shortener_url}</code>\n\n"
        "Выберите URL для изменения:"
    )
    
    kb = [
        [types.InlineKeyboardButton(text="📝 Bastart API URL", callback_data="set_api_url")],
        [types.InlineKeyboardButton(text="📝 Shortener URL", callback_data="set_shortener_url")],
        [types.InlineKeyboardButton(text="♻️ Сбросить на стандартные", callback_data="reset_api_urls")],
        [types.InlineKeyboardButton(text="🔙 Назад", callback_data="open_api_settings")]
    ]
    
    await callback.message.edit_text(
        text,
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode="HTML"
    )

# Обработчики ввода URL
@router.callback_query(F.data == "set_api_url")
async def set_api_url(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text(
        "🌐 Введите <b>URL Bastart API</b>:\n"
        "По умолчанию: https://web-api.bdev.su/",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="❌ Отмена", callback_data="api_urls_menu")]
        ]),
        parse_mode="HTML"
    )
    await state.set_state(SettingsFSM.waiting_for_api_url)

@router.callback_query(F.data == "set_shortener_url")
async def set_shortener_url(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text(
        "🌐 Введите <b>URL Shortener API</b>:\n"
        "По умолчанию: http://193.233.112.8/api/shorten",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="❌ Отмена", callback_data="api_urls_menu")]
        ]),
        parse_mode="HTML"
    )
    await state.set_state(SettingsFSM.waiting_for_shortener_url)

@router.message(SettingsFSM.waiting_for_api_url, F.text)
async def receive_api_url(message: types.Message, state: FSMContext):
    url = message.text.strip()
    if not url.endswith("/"):
        url += "/"
    save_api_setting("bastart_api_url", url)
    await message.answer(f"✅ Bastart API URL сохранен!")
    await state.clear()
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔙 К URL", callback_data="api_urls_menu")]
    ])
    await message.answer("URL установлен", reply_markup=kb)

@router.message(SettingsFSM.waiting_for_shortener_url, F.text)
async def receive_shortener_url(message: types.Message, state: FSMContext):
    url = message.text.strip()
    save_api_setting("shortener_api_url", url)
    await message.answer(f"✅ Shortener URL сохранен!")
    await state.clear()
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔙 К URL", callback_data="api_urls_menu")]
    ])
    await message.answer("URL установлен", reply_markup=kb)

# Сброс URL на стандартные
@router.callback_query(F.data == "reset_api_urls")
async def reset_api_urls(callback: types.CallbackQuery):
    save_api_setting("bastart_api_url", "https://web-api.bdev.su/")
    save_api_setting("shortener_api_url", "http://193.233.112.8/api/shorten")
    await callback.answer("✅ URL сброшены на стандартные", show_alert=True)
    await api_urls_menu(callback)



# Заменяем обработчик set_api_price на версию с пресетами
@router.callback_query(F.data == "set_api_price")
async def set_api_price(callback: types.CallbackQuery):
    """Выбор цены из пресетов или ввод своей"""
    await callback.answer()
    
    api_settings = get_api_settings()
    current_price = api_settings.get("default_price", 0.11)
    
    # Пресеты цен
    presets = [0.10, 0.11, 0.50, 1.00, 5.00, 10.00]
    
    kb = []
    # Добавляем пресеты
    row = []
    for price in presets:
        mark = "✅ " if price == current_price else ""
        row.append(
            types.InlineKeyboardButton(
                text=f"{mark}{price:.2f}",
                callback_data=f"api_price_preset:{price}"
            )
        )
        if len(row) == 3:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
    
    kb.append([
        types.InlineKeyboardButton(text="✍️ Ввести свою цену", callback_data="api_price_custom")
    ])
    kb.append([
        types.InlineKeyboardButton(text="🔙 Назад", callback_data="api_service_menu")
    ])
    
    await callback.message.edit_text(
        f"💰 <b>Установка цены</b>\n\n"
        f"Текущая цена: <code>{current_price}</code>\n\n"
        f"Выберите из пресетов или введите свою:",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode="HTML"
    )

# Добавляем новые обработчики для цены
@router.callback_query(F.data.startswith("api_price_preset:"))
async def api_price_preset(callback: types.CallbackQuery):
    """Установить цену из пресета"""
    price = float(callback.data.split(":", 1)[1])
    save_api_setting("default_price", price)
    await callback.answer(f"✅ Цена установлена: {price}", show_alert=True)
    await api_service_menu(callback)

@router.callback_query(F.data == "api_price_custom")
async def api_price_custom(callback: types.CallbackQuery, state: FSMContext):
    """Ввод своей цены"""
    await callback.answer()
    await callback.message.edit_text(
        "💰 Введите <b>цену</b> (например: 0.11 или 5.50):",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="❌ Отмена", callback_data="set_api_price")]
        ]),
        parse_mode="HTML"
    )
    await state.set_state(SettingsFSM.waiting_for_price)

@router.message(SettingsFSM.waiting_for_price, F.text)
async def receive_price(message: types.Message, state: FSMContext):
    try:
        price = float(message.text.strip().replace(",", "."))
        save_api_setting("default_price", price)
        await message.answer(f"✅ Цена установлена: {price}")
        await state.clear()
        
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔙 К настройкам сервиса", callback_data="api_service_menu")]
        ])
        await message.answer("Готово", reply_markup=kb)
    except ValueError:
        await message.answer("❌ Ошибка! Введите число (например: 0.11).")



# Тест API
@router.callback_query(F.data == "api_test")
async def api_test(callback: types.CallbackQuery):
    """Тестирование API"""
    await callback.answer("🔄 Тестирование...")
    
    api_settings = get_api_settings()
    
    # Тест Bastart API
    headers = {
        "X-Team-Token": api_settings.get("bastart_project_token", ""),
        "X-User-Token": api_settings.get("bastart_worker_token", ""),
        "Content-Type": "application/json"
    }
    
    data = {
        "platform_id": api_settings.get("default_platform_id", 1),
        "profile_id": api_settings.get("default_profile_id", 379783),
        "title": "Test",
        "price": api_settings.get("default_price", 0.11)
    }
    
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                api_settings.get("bastart_api_url", "https://web-api.bdev.su/"),
                headers=headers,
                json=data
            ) as resp:
                if resp.status == 201:
                    result = await resp.json()
                    text = (
                        "✅ <b>API работает!</b>\n\n"
                        f"Тестовая ссылка:\n<code>{result.get('link', 'нет ссылки')}</code>"
                    )
                else:
                    error_text = await resp.text()
                    text = f"❌ Ошибка API: HTTP {resp.status}\n{error_text[:200]}"
    except Exception as e:
        text = f"❌ Ошибка: {str(e)}"
    
    kb = [[types.InlineKeyboardButton(text="🔙 Назад", callback_data="open_api_settings")]]
    
    await callback.message.edit_text(
        text,
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode="HTML"
    )

# Старый обработчик test_api_settings для совместимости
@router.callback_query(F.data == "test_api_settings")
async def test_api_settings(callback: types.CallbackQuery):
    await api_test(callback)

# ============= КОНЕЦ НАСТРОЕК API =============

@router.callback_query(F.data == "open_autostart_settings")
async def open_autostart_settings(callback: types.CallbackQuery):
    await callback.answer()
    s = get_settings()
    await callback.message.edit_text(build_autostart_caption(s), reply_markup=get_autostart_menu(s), parse_mode="HTML")

@router.callback_query(F.data == "open_fingerprint_settings")
async def open_fingerprint_settings(callback: types.CallbackQuery):
    s = get_settings()
    await callback.answer()
    await callback.message.edit_text(build_fingerprint_caption(s), reply_markup=get_fingerprint_menu(s), parse_mode="HTML")

@router.callback_query(F.data == "back_to_fingerprint")
async def back_to_fingerprint(callback: types.CallbackQuery):
    await open_fingerprint_settings(callback)

@router.callback_query(F.data == "noop")
async def noop(callback: types.CallbackQuery):
    await callback.answer()

# Вспомогательная функция для сохранения User-Agents
def _save_user_agents(lines: List[str]) -> int:
    """Сохранить список User-Agents"""
    ua_file = "user_agents.json"
    unique_agents = []
    
    for line in lines:
        line = line.strip()
        if line and len(line) > 10 and line not in unique_agents:
            unique_agents.append(line)
    
    if unique_agents:
        try:
            with open(ua_file, 'w', encoding='utf-8') as f:
                json.dump(unique_agents, f, ensure_ascii=False, indent=2)
            
            set_setting("ua_source", "file")
            set_setting("ua_count", len(unique_agents))
        except Exception as e:
            print(f"Error saving user agents: {e}")
            return 0
    
    return len(unique_agents)

# Общие тумблеры
@router.callback_query(F.data == "toggle_browser_visible")
async def toggle_browser_visible(callback: types.CallbackQuery):
    s = get_settings(); s['browser_visible'] = not s.get('browser_visible', False)
    set_setting('browser_visible', s['browser_visible'])
    await callback.answer(f"Видимость: {'Включена' if s['browser_visible'] else 'Отключена'}")
    await callback.message.edit_reply_markup(reply_markup=get_common_menu(s))

@router.callback_query(F.data == "toggle_without_proxy")
async def toggle_without_proxy(callback: types.CallbackQuery):
    s = get_settings(); s['without_proxy'] = not s.get('without_proxy', False)
    set_setting('without_proxy', s['without_proxy'])
    await callback.answer(f"Без прокси: {'Вкл' if s['without_proxy'] else 'Выкл'}")
    await callback.message.edit_reply_markup(reply_markup=get_common_menu(s))

@router.callback_query(F.data == "toggle_without_accounts")
async def toggle_without_accounts(callback: types.CallbackQuery):
    s = get_settings(); s['without_accounts'] = not s.get('without_accounts', False)
    set_setting('without_accounts', s['without_accounts'])
    await callback.answer(f"Без аккаунтов: {'Вкл' if s['without_accounts'] else 'Выкл'}")
    await callback.message.edit_reply_markup(reply_markup=get_common_menu(s))

@router.callback_query(F.data == "toggle_text_rotation")
async def toggle_text_rotation(callback: types.CallbackQuery):
    s = get_settings()
    s['text_rotation'] = not s.get('text_rotation', False)
    set_setting('text_rotation', s['text_rotation'])
    await callback.answer(f"Ротация текстов: {'Вкл' if s['text_rotation'] else 'Выкл'}")
    await callback.message.edit_reply_markup(reply_markup=get_common_menu(s))

# Автозапуск
@router.callback_query(F.data == "set_autostart_timer")
async def set_autostart_timer(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text("Укажите время автозапуска в секундах (0 для отключения):", reply_markup=get_back_menu())
    await state.set_state(SettingsFSM.waiting_for_timer)

@router.callback_query(F.data.startswith("set_autostart_preset:"))
async def set_autostart_preset(callback: types.CallbackQuery):
    _, val = callback.data.split(":", 1)
    secs = int(val) if val.isdigit() else 0
    set_setting("autostart_timer", secs if secs > 0 else None)
    await callback.answer(f"Таймер: {secs if secs > 0 else 'Отключен'}")
    s = get_settings()
    await callback.message.edit_text(build_autostart_caption(s), reply_markup=get_autostart_menu(s), parse_mode="HTML")
    try:
        import handlers.main_menu as main_menu_module
        await main_menu_module.restart_auto_start_timer(callback.bot)
    except Exception as e:
        print(f"[SETTINGS] Ошибка перезапуска автозапуска: {e}")

@router.message(SettingsFSM.waiting_for_timer, F.text)
async def receive_timer(message: types.Message, state: FSMContext, bot: Bot):
    try:
        timer = int(message.text.strip())
        set_setting('autostart_timer', timer if timer > 0 else None)
        s = get_settings()
        await message.answer(build_autostart_caption(s), reply_markup=get_autostart_menu(s), parse_mode="HTML")
        try:
            import handlers.main_menu as main_menu_module
            await main_menu_module.restart_auto_start_timer(bot)
        except Exception as e:
            print(f"[SETTINGS] Ошибка перезапуска таймера: {e}")
    except Exception:
        await message.answer("Ошибка! Введите число.")
    await state.clear()

# Антидетект — UA/Resolutions
@router.callback_query(F.data == "toggle_ua_source")
async def toggle_ua_source(callback: types.CallbackQuery):
    s = get_settings(); current = s.get("ua_source", "random")
    new_val = "file" if current != "file" else "random"
    set_setting("ua_source", new_val)
    await callback.answer(f"Источник UA: {'файл' if new_val == 'file' else 'рандом'}")
    s = get_settings()
    await callback.message.edit_text(build_fingerprint_caption(s), reply_markup=get_fingerprint_menu(s), parse_mode="HTML")

@router.callback_query(F.data == "upload_ua_file")
async def upload_ua_file(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("Пришлите .txt файл или список UA текстом.")
    await callback.message.edit_text("Пришлите .txt файл с User-Agent (каждый на новой строке) или отправьте список текстом.", reply_markup=get_back_menu())
    await state.set_state(SettingsFSM.waiting_for_ua_file)

@router.message(SettingsFSM.waiting_for_ua_file, F.document)
async def receive_ua_file_document(message: types.Message, state: FSMContext):
    doc = message.document
    if not doc or (doc.file_name and not doc.file_name.lower().endswith(".txt")):
        await message.answer("Нужен .txt файл.")
        return
    buf = io.BytesIO()
    await message.bot.download(doc, destination=buf)
    buf.seek(0)
    content = buf.read().decode("utf-8", errors="ignore")
    lines = [l.strip() for l in content.splitlines()]
    count = _save_user_agents(lines)
    await message.answer(f"Файл загружен. Уникальных UA: {count}", reply_markup=get_fingerprint_menu(get_settings()), parse_mode="HTML")
    await state.clear()

@router.message(SettingsFSM.waiting_for_ua_file, F.text)
async def receive_ua_file_text(message: types.Message, state: FSMContext):
    lines = [l.strip() for l in message.text.splitlines()]
    count = _save_user_agents(lines)
    await message.answer(f"Принято. Уникальных UA: {count}", reply_markup=get_fingerprint_menu(get_settings()), parse_mode="HTML")
    await state.clear()

@router.callback_query(F.data == "toggle_random_resolution")
async def toggle_random_resolution(callback: types.CallbackQuery):
    s = get_settings(); flag = not s.get("random_resolution", True)
    set_setting("random_resolution", flag)
    await callback.answer(f"Рандомное разрешение: {'вкл' if flag else 'выкл'}")
    s = get_settings()
    await callback.message.edit_text(build_fingerprint_caption(s), reply_markup=get_fingerprint_menu(s), parse_mode="HTML")

@router.callback_query(F.data == "open_resolution_menu")
async def open_resolution_menu(callback: types.CallbackQuery):
    s = get_settings()
    await callback.answer()
    await callback.message.edit_text("<b>Выбор разрешения экрана</b>\nПК-пресеты (≥1440×900) или введите своё.", reply_markup=get_resolution_menu(s.get("screen_resolution"), s.get("random_resolution", True)), parse_mode="HTML")

@router.callback_query(F.data.startswith("set_resolution:"))
async def set_resolution(callback: types.CallbackQuery):
    _, value = callback.data.split(":", 1)
    if value == "random":
        set_setting("random_resolution", True); set_setting("screen_resolution", None)
        await callback.answer("Режим рандома включён.")
    else:
        if not re.fullmatch(r"\d{2,4}x\d{2,4}", value):
            await callback.answer("Неверный формат.")
            return
        set_setting("random_resolution", False); set_setting("screen_resolution", value)
        await callback.answer(f"Разрешение: {value}")
    s = get_settings()
    await callback.message.edit_text("<b>Выбор разрешения экрана</b>\nПК-пресеты (≥1440×900) или введите своё.", reply_markup=get_resolution_menu(s.get("screen_resolution"), s.get("random_resolution", True)), parse_mode="HTML")

@router.callback_query(F.data == "enter_custom_resolution")
async def enter_custom_resolution(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text("Введите разрешение в формате ШxВ, например 1920x1080", reply_markup=get_back_menu())
    await state.set_state(SettingsFSM.waiting_for_custom_resolution)

@router.message(SettingsFSM.waiting_for_custom_resolution, F.text)
async def receive_custom_resolution(message: types.Message, state: FSMContext):
    text = message.text.strip().lower().replace(" ", "")
    m = re.fullmatch(r"(\d{2,4})x(\d{2,4})", text)
    if not m:
        await message.answer("Неверный формат. Пример: 1920x1080")
        return
    w, h = int(m.group(1)), int(m.group(2))
    set_setting("random_resolution", False); set_setting("screen_resolution", f"{w}x{h}")
    await message.answer("🕵️ Возврат в антидетект", reply_markup=get_fingerprint_menu(get_settings()), parse_mode="HTML")
    await state.clear()

# Антидетект — Устройство
@router.callback_query(F.data == "open_hardware_settings")
async def open_hardware_settings(callback: types.CallbackQuery):
    s = get_settings()
    await callback.answer()
    await callback.message.edit_text("🧠 <b>Устройство</b>\nНастройте GPU/шумы/платформу/CPU/память.", reply_markup=get_hardware_menu(s), parse_mode="HTML")

@router.callback_query(F.data == "toggle_hw_source")
async def toggle_hw_source(callback: types.CallbackQuery):
    s = get_settings(); cur = s.get("hw_source", "auto")
    newv = "custom" if cur == "auto" else "auto"
    set_setting("hw_source", newv)
    await callback.answer(f"Источник: {newv}")
    await callback.message.edit_reply_markup(reply_markup=get_hardware_menu(get_settings()))

@router.callback_query(F.data == "cycle_hw_gpu_vendor")
async def cycle_hw_gpu_vendor(callback: types.CallbackQuery):
    order = ["auto", "Intel", "NVIDIA", "AMD", "Apple"]
    s = get_settings(); cur = s.get("hw_gpu_vendor", "auto")
    nxt = order[(order.index(cur) + 1) % len(order)] if cur in order else "Intel"
    set_setting("hw_gpu_vendor", nxt)
    set_setting("hw_gpu_model", "auto")
    await callback.answer(f"GPU вендор: {nxt}")
    await callback.message.edit_reply_markup(reply_markup=get_hardware_menu(get_settings()))

@router.callback_query(F.data == "cycle_hw_gpu_model")
async def cycle_hw_gpu_model(callback: types.CallbackQuery):
    from utils.device_profiles import GPU_MODELS
    s = get_settings()
    vendor = s.get("hw_gpu_vendor", "auto")
    if vendor == "auto":
        await callback.answer("Сначала выберите вендора.")
        return
    models = ["auto"] + (GPU_MODELS.get(vendor, []) or [])
    cur = s.get("hw_gpu_model", "auto")
    try:
        idx = models.index(cur)
    except ValueError:
        idx = 0
    nxt = models[(idx + 1) % len(models)]
    set_setting("hw_gpu_model", nxt)
    await callback.answer(f"Модель: {nxt}")
    await callback.message.edit_reply_markup(reply_markup=get_hardware_menu(get_settings()))

@router.callback_query(F.data == "cycle_hw_noise")
async def cycle_hw_noise(callback: types.CallbackQuery):
    order = ["low", "medium", "high"]
    s = get_settings(); cur = s.get("hw_noise_level", "medium")
    nxt = order[(order.index(cur) + 1) % len(order)] if cur in order else "medium"
    set_setting("hw_noise_level", nxt)
    await callback.answer(f"Шум: {nxt}")
    await callback.message.edit_reply_markup(reply_markup=get_hardware_menu(get_settings()))

@router.callback_query(F.data == "cycle_hw_hc")
async def cycle_hw_hc(callback: types.CallbackQuery):
    order = ["auto", "8", "12", "16", "20"]
    s = get_settings(); cur = str(s.get("hw_hc", "auto"))
    nxt = order[(order.index(cur) + 1) % len(order)] if cur in order else "8"
    set_setting("hw_hc", None if nxt == "auto" else int(nxt))
    await callback.answer(f"CPU threads: {nxt}")
    await callback.message.edit_reply_markup(reply_markup=get_hardware_menu(get_settings()))

@router.callback_query(F.data == "cycle_hw_mem")
async def cycle_hw_mem(callback: types.CallbackQuery):
    order = ["auto", "8", "16", "32"]
    s = get_settings(); cur = str(s.get("hw_mem", "auto"))
    nxt = order[(order.index(cur) + 1) % len(order)] if cur in order else "16"
    set_setting("hw_mem", None if nxt == "auto" else int(nxt))
    await callback.answer(f"Memory: {nxt}")
    await callback.message.edit_reply_markup(reply_markup=get_hardware_menu(get_settings()))

@router.callback_query(F.data == "cycle_hw_platform")
async def cycle_hw_platform(callback: types.CallbackQuery):
    order = ["auto", "Win32", "MacIntel"]
    s = get_settings(); cur = s.get("hw_platform_override", "auto")
    nxt = order[(order.index(cur) + 1) % len(order)] if cur in order else "Win32"
    set_setting("hw_platform_override", nxt)
    await callback.answer(f"Платформа: {nxt}")
    await callback.message.edit_reply_markup(reply_markup=get_hardware_menu(get_settings()))

@router.callback_query(F.data == "toggle_hw_mtp")
async def toggle_hw_mtp(callback: types.CallbackQuery):
    s = get_settings(); cur = int(s.get("hw_max_touch_points", 0) or 0)
    nxt = 0 if cur != 0 else 1
    set_setting("hw_max_touch_points", nxt)
    await callback.answer(f"maxTouchPoints: {nxt}")
    await callback.message.edit_reply_markup(reply_markup=get_hardware_menu(get_settings()))

@router.callback_query(F.data == "cycle_hw_cdepth")
async def cycle_hw_cdepth(callback: types.CallbackQuery):
    order = [24, 30]
    s = get_settings(); cur = int(s.get("hw_color_depth", 24) or 24)
    nxt = order[(order.index(cur) + 1) % len(order)]
    set_setting("hw_color_depth", int(nxt))
    await callback.answer(f"ColorDepth: {nxt}")
    await callback.message.edit_reply_markup(reply_markup=get_hardware_menu(get_settings()))