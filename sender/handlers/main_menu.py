import asyncio
import random
import html
import requests
import inspect
from urllib.parse import quote
from db import get_blacklisted_seller_count
from aiogram import Router, F, types, Bot
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from keyboards.main_menu import (
    get_main_menu,
    get_back_menu,
    get_browser_control_keyboard,
    get_manage_browsers_keyboard,
    get_manage_browsers_list_keyboard,
)
from handlers.proxy_accounts import proxy_menu
from handlers.platforms import router as platforms_router, platforms_menu
from handlers.settings import show_settings
from db import (
    get_proxies,
    get_accounts,
    get_settings,
    get_platform_settings,
    save_user,
    get_user,
    get_stats,
    set_last_mailing_start,
    set_last_mailing_end,
    get_cookie_accounts,
)
from utils.account_pool import AccountPool
from aiogram.types import FSInputFile, URLInputFile
import os

# Антидетект
from utils.fingerprint import FingerprintAllocator
from utils import ua_store
from utils.geo import resolve_geo_via_proxy
from utils.anti_profile import build_context_overrides

from typing import Optional, Dict, Any


router = Router()
router.event_types = {"message", "callback_query"}
router.include_router(platforms_router)

ACTIVE_BROWSERS = {}
BROWSER_COUNTER = 0
PLATFORMS = ["krisha", "kolesa", "lalafo"]
MAX_TELEGRAM_MESSAGE_LENGTH = 4096
AUTO_START_TASK = None

# Общий словарь для хранения состояния аккаунтов
SHARED_ACCOUNT_STATE = {}

# --- ДОБАВИТЬ: Функция для автозакрытия всех браузеров ---
async def close_all_browsers_force(bot: Bot = None):
    closed_count = len(ACTIVE_BROWSERS)
    for bid, data in ACTIVE_BROWSERS.copy().items():
        if data["task"]:
            data["task"].cancel()
    ACTIVE_BROWSERS.clear()
    # Уведомление админу (через бота, если передан)
    if bot and closed_count > 0:
        try:
            from config import ADMIN_IDS
            for admin_id in ADMIN_IDS:
                await bot.send_message(
                    admin_id,
                    f"🛑 <b>Все браузеры ({closed_count}) были закрыты перед автозапуском рассылки (по таймеру)</b>",
                    parse_mode="HTML"
                )
        except Exception as e:
            print(f"[AUTO CLOSE] Не удалось отправить уведомление админу: {e}")


def distribute_categories(categories, num_workers):
    if num_workers == 0:
        return []
    random.shuffle(categories)
    n = len(categories)
    base = n // num_workers
    remainder = n % num_workers
    result = []
    idx = 0
    for i in range(num_workers):
        count = base + (1 if i < remainder else 0)
        worker_cats = categories[idx: idx + count]
        result.append(worker_cats)
        idx += count
    return result


def build_playwright_proxy_from_row(row) -> dict | None:
    if not row:
        return None
    _, ip, port, username, password, protocol = (row + (None,))[:6]
    scheme = (protocol or "http").lower()
    if not ip or not port:
        return None
    conf = {"server": f"{scheme}://{ip}:{port}"}
    if username and password:
        conf["username"] = str(username)
        conf["password"] = str(password)
    return conf


def build_proxy_url_for_requests(row) -> str | None:
    if not row:
        return None
    _, ip, port, username, password, protocol = (row + (None,))[:6]
    scheme = (protocol or "http").lower()
    if not ip or not port:
        return None
    if username and password:
        return f"{scheme}://{quote(str(username))}:{quote(str(password))}@{ip}:{port}"
    return f"{scheme}://{ip}:{port}"


def proxy_display_from_row(row) -> str:
    if not row:
        return "Без прокси"
    _, ip, port, username, password, protocol = (row + (None,))[:6]
    scheme = (protocol or "http").lower()
    disp = f"{scheme}://{ip}:{port}"
    if username and password:
        disp += " (auth)"
    return disp


async def update_worker_log(bot: Bot, chat_id: int, message_id: int, log_lines: list):
    text = "\n".join(log_lines)
    if len(text) > MAX_TELEGRAM_MESSAGE_LENGTH:
        text = text[-MAX_TELEGRAM_MESSAGE_LENGTH:]
    try:
        await bot.edit_message_text(
            text=text,
            chat_id=chat_id,
            message_id=message_id,
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"[LOG ERROR] Cannot update message {message_id}: {e}")


async def update_browser_message(bot: Bot, browser_id: int):
    data = ACTIVE_BROWSERS.get(browser_id)
    if not data:
        return
    text = "\n".join(data["log_lines"])
    if len(text) > MAX_TELEGRAM_MESSAGE_LENGTH:
        text = text[-MAX_TELEGRAM_MESSAGE_LENGTH:]
    try:
        await bot.edit_message_text(
            text=text,
            chat_id=data["chat_id"],
            message_id=data["message_id"],
            parse_mode="HTML",
            reply_markup=get_browser_control_keyboard(data["status"]),
        )
    except Exception as e:
        print(f"[ERROR] Failed to update browser {browser_id}: {e}")


async def update_manage_browsers_menu(bot: Bot, chat_id: int = None, message_id: int = None):
    text = "📭 Нет запущенных браузеров"
    if ACTIVE_BROWSERS:
        text = "🟢 <b>Запущенные браузеры:</b>\n\n"
        for bid, data in ACTIVE_BROWSERS.items():
            status = "⏸️ Приостановлен" if data["status"] == "paused" else "▶️ Работает"
            username_display = data['username'] if data['username'] else "Без аккаунта"
            text += (
                f"📌 <b>#{bid}</b> | {data['platform'].upper()} | {username_display}\n"
                f"🔹 Статус: {status}\n"
                f"🔹 Прокси: {data['proxy'] or 'Без прокси'}\n\n"
            )
    if chat_id and message_id:
        try:
            await bot.edit_message_text(
                text=text,
                chat_id=chat_id,
                message_id=message_id,
                parse_mode="HTML",
                reply_markup=get_manage_browsers_list_keyboard(ACTIVE_BROWSERS)
            )
        except Exception as e:
            print(f"[ERROR] Failed to update manage browsers menu: {e}")


# ================== НОРМАЛИЗАЦИЯ РЕЗУЛЬТАТОВ ВОРКЕРА ==================
BAN_RESULTS = {
    False,
    "invalid", "ban", "banned", "blocked",
    "limited", "limit", "restricted", "account_restricted",
    "account_blocked",
    "invalid_credentials",
    "auth_failed",
    "captcha_lock",
    "session_lost",
    "other_worker_banned",
    # Добавляем варианты для ограничений
    "account_limited",
    "message_limit_reached",
    "fraud_detected",
    "restricted_messaging",
}
PROXY_RESULTS = {
    "proxy_error", "network_error", "timeout_proxy", "proxy_fail", "net_timeout",
    "import_error",
}
ERROR_RESULTS = {"error"}
SUCCESS_RESULTS = {True, "ok", "success", "done"}


def classify_worker_result(result):
    auth_ok = None
    status = result
    
    # Обработка словарей
    if isinstance(result, dict):
        status = result.get("status")
        auth_ok = result.get("auth_ok")
        # Дополнительная проверка reason
        if result.get("reason") in ["account_blocked", "restricted", "invalid_credentials", "account_restricted"]:
            return "ban", auth_ok
    
    # ВАЖНО: False означает что аккаунт ограничен/забанен
    if result is False:
        return "ban", auth_ok
    # ВАЖНО: None и True означают успешное завершение
    if result is None or result is True:
        return "success", auth_ok
        
    # Обработка строк напрямую
    if isinstance(result, str):
        key = result.strip().lower()
        # Прямые строковые результаты от воркеров
        if result in ["invalid_credentials", "account_blocked", "account_restricted", "restricted"]:
            return "ban", auth_ok
        if result == "proxy_error":
            return "proxy", auth_ok
        if result == "auth_failed":
            return "ban", auth_ok
    
    # Нормализация ключа
    if isinstance(status, str):
        key = status.strip().lower()
    else:
        key = status

    if key in PROXY_RESULTS:
        return "proxy", auth_ok
    if key in BAN_RESULTS or auth_ok is False:
        return "ban", auth_ok
    if key in ERROR_RESULTS:
        return "error", auth_ok
    if key in SUCCESS_RESULTS:
        return "success", auth_ok
    
    # По умолчанию считаем успехом (включая None)
    return "success", auth_ok


def _delete_fp(username: str | None, platform_a: str, platform_b: str | None, sync_devices: bool):
    if not username:
        return
    try:
        if sync_devices:
            ua_store.delete_fingerprint(f"shared:{username}")
        else:
            ua_store.delete_fingerprint(f"{platform_a}:{username}")
            if platform_b:
                ua_store.delete_fingerprint(f"{platform_b}:{username}")
    except Exception as e:
        print(f"[UA_STORE] FP cleanup error for {username}: {e}")


async def build_fp_and_context_for_account(
    account_key: str | None,
    settings: dict,
    fp_allocator: FingerprintAllocator,
    proxy_requests_url: str | None,
    persist_fingerprint: bool
):
    ua, viewport = fp_allocator.for_account(
        account_key=account_key,
        persist=persist_fingerprint
    )
    try:
        geo = await resolve_geo_via_proxy(proxy_requests_url) if proxy_requests_url else None
    except Exception:
        geo = None
    context_overrides = build_context_overrides(viewport=viewport, geo=geo)

    stealth_js = None
    try:
        from utils.anti_profile import build_stealth_js
        from utils.device_profiles import (
            detect_os_from_ua,
            default_platform_for_os,
            pick_vendor_for_os,
            pick_gpu_model,
            build_renderer_for_os,
        )

        device_fp = ua_store.get_device_fp(account_key) if (account_key and persist_fingerprint) else None
        if not device_fp:
            s = settings
            hw_src = s.get("hw_source", "auto")
            os_name = detect_os_from_ua(ua or "")

            if hw_src == "custom":
                vendor = s.get("hw_gpu_vendor", "auto")
                if vendor == "auto":
                    vendor = pick_vendor_for_os(os_name)
                model = s.get("hw_gpu_model", "auto")
                if model == "auto":
                    model = pick_gpu_model(vendor)
            else:
                vendor = pick_vendor_for_os(os_name)
                model = pick_gpu_model(vendor)

            webgl_vendor, webgl_renderer = build_renderer_for_os(os_name, vendor, model)
            platform_override = s.get("hw_platform_override", "auto")
            platform_str = default_platform_for_os(os_name) if platform_override == "auto" else platform_override
            hw_hc = int(s.get("hw_hc")) if s.get("hw_hc") else random.choice([8, 12, 16])
            hw_mem = int(s.get("hw_mem")) if s.get("hw_mem") else random.choice([8, 16])
            hw_mtp = int(s.get("hw_max_touch_points", 0) or 0)
            color_depth = int(s.get("hw_color_depth", 24) or 24)
            noise_level = s.get("hw_noise_level", "medium")

            device_fp = {
                "gpu_vendor": vendor,
                "gpu_model": model,
                "webgl_vendor": webgl_vendor,
                "webgl_renderer": webgl_renderer,
                "platform_str": platform_str,
                "device_memory": hw_mem,
                "hardware_concurrency": hw_hc,
                "max_touch_points": hw_mtp,
                "color_depth": color_depth,
                "noise_level": noise_level,
            }
            if account_key and persist_fingerprint:
                ua_store.set_device_fp(account_key, device_fp)

        stealth_js = build_stealth_js({
            "platform_str": device_fp.get("platform_str"),
            "hardware_concurrency": device_fp.get("hardware_concurrency"),
            "device_memory": device_fp.get("device_memory"),
            "max_touch_points": device_fp.get("max_touch_points"),
            "color_depth": device_fp.get("color_depth"),
            "webgl_vendor": device_fp.get("webgl_vendor"),
            "webgl_renderer": device_fp.get("webgl_renderer"),
            "noise_level": device_fp.get("noise_level"),
        })
    except Exception as e:
        stealth_js = None
    return ua, viewport, context_overrides, stealth_js


async def start_mailing_core(
    bot: Bot,
    chat_id: int,
    callback: types.CallbackQuery = None
):
    has_callback = callback is not None and callback.message is not None
    if has_callback:
        await callback.answer()

    # Очищаем словарь состояния аккаунтов перед каждым запуском
    global SHARED_ACCOUNT_STATE
    SHARED_ACCOUNT_STATE.clear()
    
    set_last_mailing_start()
    proxies = get_proxies()
    settings = get_settings()
    without_proxy = settings.get("without_proxy", False)
    without_accounts = settings.get("without_accounts", False)
    visible_browser = settings.get("browser_visible", False)
    headless = not visible_browser

    # Настройки последовательного запуска
    sync_devices = settings.get("sync_device_cross_platform", True)
    rr_delay = settings.get("launch_rr_delay", 1)
    pair_secondary_delay_sec = float(settings.get("pair_secondary_delay_sec") or 6)
    pair_cancel_on_ban = bool(settings.get("pair_cancel_on_ban", True))

    fp_allocator = FingerprintAllocator(settings)

    enabled_platforms = []
    for platform in PLATFORMS:
        plat_settings = get_platform_settings(platform)
        if plat_settings.get("multithread", False):
            enabled_platforms.append(platform)

    account_pool = AccountPool(get_accounts())
    cookie_accounts = get_cookie_accounts() if "lalafo" in enabled_platforms else []

    non_lalafo_platforms = [p for p in enabled_platforms if p != "lalafo"]
    needs_regular_accounts = bool(non_lalafo_platforms) and not without_accounts

    if needs_regular_accounts and await account_pool.is_empty():
        txt = "❗ Нет загруженных аккаунтов для Krisha/Kolesa. Загрузите хотя бы один или включите 'Работа без аккаунтов'."
        if has_callback:
            await callback.answer(txt, show_alert=True)
        else:
            await bot.send_message(chat_id, txt)
        set_last_mailing_end()
        return

    if "lalafo" in enabled_platforms and not without_accounts and not cookie_accounts:
        txt = "❗ Нет cookie-аккаунтов для Lalafo. Загрузите или включите режим 'Работа без аккаунтов'."
        if has_callback:
            await callback.answer(txt, show_alert=True)
        else:
            await bot.send_message(chat_id, txt)
        set_last_mailing_end()
        return

    if not enabled_platforms:
        txt = "❗ Не включён мультипоток ни на одной площадке."
        if has_callback:
            await callback.answer(txt, show_alert=True)
        else:
            await bot.send_message(chat_id, txt)
        set_last_mailing_end()
        return

    if not proxies and not without_proxy:
        txt = "❗ Нет прокси. Загрузите или включите 'Работа без прокси'."
        if has_callback:
            await callback.answer(txt, show_alert=True)
        else:
            await bot.send_message(chat_id, txt)
        set_last_mailing_end()
        return

    paired_active = ("krisha" in enabled_platforms) and ("kolesa" in enabled_platforms) and not without_accounts
    print(f"[PAIR MODE] {'ON' if paired_active else 'OFF'} (both_on={('krisha' in enabled_platforms and 'kolesa' in enabled_platforms)}, without_accounts={without_accounts})")

    tasks = []
    
    # Подготовка независимых воркеров для krisha/kolesa когда они НЕ в паре
    independent_specs = []
    
    if not paired_active:
        # Обрабатываем krisha и kolesa как независимые, когда не в парном режиме
        for platform in ["krisha", "kolesa"]:
            if platform not in enabled_platforms:
                continue
                
            plat_settings = get_platform_settings(platform)
            categories = plat_settings.get("categories", []) or []
            try:
                browser_count = int(plat_settings.get("browser_count", 1) or 1)
            except Exception:
                browser_count = 1
            try:
                max_proxies_per_account = int(plat_settings.get("max_proxies_per_account") or 1)
            except Exception:
                max_proxies_per_account = 1
                
            accounts_available = len(account_pool._accounts) if not without_accounts else float('inf')
            proxies_available = len(proxies) if proxies else 0
            categories_count = len(categories)
            
            if not without_proxy and proxies:
                max_accounts_by_proxies = min(accounts_available, proxies_available * max_proxies_per_account)
            else:
                max_accounts_by_proxies = accounts_available
                
            real_browser_count = min(
                browser_count,
                max_accounts_by_proxies if not without_accounts else browser_count,
                categories_count if categories_count > 0 else browser_count
            )
            
            proxy_cycle = []
            if proxies and not without_proxy:
                for _ in range(max_proxies_per_account):
                    proxy_cycle.extend(proxies)
                    
            if real_browser_count > 0:
                cats_for_workers = (
                    [categories[:]] if real_browser_count == 1
                    else (distribute_categories(categories, real_browser_count) if categories else [[] for _ in range(real_browser_count)])
                )
                
                for j in range(real_browser_count):
                    acc = None
                    if not without_accounts:
                        acc = await account_pool.take()
                        if not acc:
                            break
                            
                    proxy_conf = None
                    proxy_disp = None
                    proxy_requests_url = None
                    if not without_proxy and proxies:
                        if j < len(proxy_cycle):
                            proxy_row = proxy_cycle[j]
                            proxy_conf = build_playwright_proxy_from_row(proxy_row)
                            proxy_disp = proxy_display_from_row(proxy_row)
                            proxy_requests_url = build_proxy_url_for_requests(proxy_row)
                        else:
                            if acc and not without_accounts:
                                await account_pool.release(acc)
                            break
                            
                    username = acc[1] if acc else "Без аккаунта"
                    fp_key = f"{platform}:{username}" if not without_accounts else None
                    
                    ua, viewport, context_overrides, stealth_js = await build_fp_and_context_for_account(
                        account_key=fp_key,
                        settings=settings,
                        fp_allocator=fp_allocator,
                        proxy_requests_url=proxy_requests_url if (proxy_requests_url and not without_proxy) else None,
                        persist_fingerprint=not without_accounts
                    )
                    
                    worker_categories = cats_for_workers[j] if j < len(cats_for_workers) else []
                    worker_plat_settings = plat_settings.copy()
                    worker_plat_settings["text_rotation"] = settings.get("text_rotation", False)
                    
                    independent_specs.append({
                        "platform": platform,
                        "acc": acc,
                        "proxy": proxy_conf,
                        "proxy_disp": proxy_disp,
                        "categories": worker_categories,
                        "settings": worker_plat_settings,
                        "user_agent": ua,
                        "viewport": viewport,
                        "context_overrides": context_overrides,
                        "stealth_js": stealth_js,
                    })

    # Подготовим Lalafo очередь (cookie, общий пул прокси, независимая от пар)
    lalafo_specs: list[dict] = []
    if "lalafo" in enabled_platforms:
        platform = "lalafo"
        plat_settings = get_platform_settings(platform)
        categories = plat_settings.get("categories", []) or []
        try:
            browser_count = int(plat_settings.get("browser_count", 1) or 1)
        except Exception:
            browser_count = 1
        try:
            max_proxies_per_account = int(plat_settings.get("max_proxies_per_account") or 1)
        except Exception:
            max_proxies_per_account = 1

        accounts_available = len(cookie_accounts) if not without_accounts else float('inf')
        proxies_available = len(proxies) if proxies else 0
        categories_count = len(categories)

        if not without_proxy and proxies:
            max_accounts_by_proxies = min(accounts_available, proxies_available * max_proxies_per_account)
        else:
            max_accounts_by_proxies = accounts_available

        real_browser_count = min(
            browser_count,
            max_accounts_by_proxies if not without_accounts else browser_count,
            categories_count if categories_count > 0 else browser_count
        )

        proxy_cycle = []
        if proxies and not without_proxy:
            for _ in range(max_proxies_per_account):
                proxy_cycle.extend(proxies)

        if real_browser_count > 0:
            cats_for_workers = (
                [categories[:]] if real_browser_count == 1
                else (distribute_categories(categories, real_browser_count) if categories else [[] for _ in range(real_browser_count)])
            )
            cookie_accounts_copy = cookie_accounts.copy()

            for j in range(real_browser_count):
                acc = None
                worker_cookie_data = None
                if not without_accounts:
                    if cookie_accounts_copy:
                        cookie_acc = cookie_accounts_copy.pop(0)
                        cookie_filename = cookie_acc[1]
                        path = os.path.join(os.getcwd(), "cookies", cookie_filename)
                        if os.path.isfile(path):
                            with open(path, "r", encoding="utf-8") as f:
                                worker_cookie_data = f.read()
                            acc = (cookie_acc[0], cookie_filename, "cookie")
                        else:
                            continue
                    else:
                        break

                proxy_conf = None
                proxy_disp = None
                proxy_requests_url = None
                if not without_proxy and proxies:
                    if j < len(proxy_cycle):
                        proxy_row = proxy_cycle[j]
                        proxy_conf = build_playwright_proxy_from_row(proxy_row)
                        proxy_disp = proxy_display_from_row(proxy_row)
                        proxy_requests_url = build_proxy_url_for_requests(proxy_row)
                    else:
                        break

                username = acc[1] if acc else "Без аккаунта"
                fp_key = f"lalafo:{username}" if not without_accounts else None

                ua, viewport, context_overrides, stealth_js = await build_fp_and_context_for_account(
                    account_key=fp_key,
                    settings=settings,
                    fp_allocator=FingerprintAllocator(settings),
                    proxy_requests_url=proxy_requests_url if (proxy_requests_url and not without_proxy) else None,
                    persist_fingerprint=not without_accounts
                )

                worker_categories = cats_for_workers[j] if j < len(cats_for_workers) else []
                worker_plat_settings = plat_settings.copy()
                if worker_cookie_data:
                    worker_plat_settings["cookie_data"] = worker_cookie_data
                worker_plat_settings["text_rotation"] = settings.get("text_rotation", False)

                lalafo_specs.append({
                    "platform": platform,
                    "acc": acc,
                    "proxy": proxy_conf,
                    "proxy_disp": proxy_disp,
                    "categories": worker_categories,
                    "settings": worker_plat_settings,
                    "cookie_data": worker_plat_settings.get("cookie_data"),
                    "user_agent": ua,
                    "viewport": viewport,
                    "context_overrides": context_overrides,
                    "stealth_js": stealth_js,
                })

    # Хелпер: создать лог-сообщение и запустить один воркер
    async def start_one_worker(platform, acc, proxy_conf, proxy_disp, settings_, categories_, user_agent, viewport, context_overrides, stealth_js, manage_account, acc_shared: Optional[Dict[str, Any]] = None):
        username = acc[1] if acc else "Без аккаунта"
        try:
            log_msg = await bot.send_message(
                chat_id=chat_id,
                text=(
                    f"<b>Платформа:</b> <code>{platform}</code>\n"
                    f"<b>Аккаунт:</b> <code>{username}</code>\n"
                    f"<b>Прокси:</b> <code>{proxy_disp or 'Без прокси'}</code>\n"
                    f"<b>Категории:</b>\n<code>{chr(10).join(categories_) if categories_ else 'Нет'}</code>\n"
                    "Статус: 🕒 Запуск воркера..."
                ),
                parse_mode="HTML"
            )
            log_chat = log_msg.chat.id
            log_msg_id = log_msg.message_id
        except Exception:
            class _D: message_id=0; chat=type("c",(),{"id":chat_id})
            log_msg = _D()
            log_chat = chat_id
            log_msg_id = 0

        return asyncio.create_task(
            run_worker(
                bot=bot,
                chat_id=log_chat,
                message_id=log_msg_id,
                platform=platform,
                acc=acc,
                account_pool=account_pool,
                proxy=proxy_conf,
                headless=headless,
                platform_settings=settings_,
                categories=categories_,
                cookie_data=(settings_.get("cookie_data") if platform == "lalafo" else None),
                user_agent=user_agent,
                viewport=viewport,
                context_overrides=context_overrides,
                stealth_js=stealth_js,
                manage_account=manage_account,
                acc_shared=acc_shared,
            )
        )

    # Оркестратор пары: запускает Krisha, затем (при необходимости) Kolesa, следит за результатами и управляет аккаунтом
    async def orchestrate_pair(
        acc,
        proxy_conf,
        proxy_disp,
        s_k,
        s_o,
        c_k,
        c_o,
        user_agent,
        viewport,
        context_overrides,
        stealth_js,
        started_second_event: asyncio.Event,
    ):
        username = acc[1] if acc else "Без аккаунта"
        # Создаем общий объект для синхронизации состояния аккаунта между воркерами
        acc_shared = {"banned": False, "ban_reason": "", "auth_ok": None}

        # Запуск Krisha
        t1 = await start_one_worker("krisha", acc, proxy_conf, proxy_disp, s_k, c_k, user_agent, viewport, context_overrides, stealth_js, manage_account=False, acc_shared=acc_shared)

        try:
            # Дожидаемся завершения первого воркера или таймаута
            done, pending = await asyncio.wait({t1}, timeout=max(0.0, float(pair_secondary_delay_sec)))
        except Exception:
            done, pending = set(), {t1}

        start_second = True
        if t1.done():
            try:
                result = await t1
                cat1, auth_ok1 = classify_worker_result(result)
                acc_shared["auth_ok"] = auth_ok1
                
                if cat1 == "ban" or auth_ok1 is False:
                    acc_shared["banned"] = True
                    acc_shared["ban_reason"] = cat1
                    start_second = False
                elif cat1 == "proxy":
                    # При ошибке прокси всё равно запускаем второй воркер
                    # Но отмечаем проблему для логов
                    acc_shared["proxy_error"] = True
            except Exception as e:
                print(f"[PAIR] Ошибка обработки результата первого воркера: {e}")
                acc_shared["error"] = str(e)
                cat1, auth_ok1 = "error", None

        t2 = None
        if start_second:
            # Запускаем второй воркер (Kolesa)
            t2 = await start_one_worker("kolesa", acc, proxy_conf, proxy_disp, s_o, c_o, user_agent, viewport, context_overrides, stealth_js, manage_account=False, acc_shared=acc_shared)
            started_second_event.set()
        else:
            started_second_event.set()
            print(f"[PAIR] Второй воркер не запущен из-за проблем с первым ({acc_shared.get('ban_reason', 'unknown')})")

        cats = []
        res1 = None
        res2 = None

        # Собираем результаты Krisha
        try:
            if not t1.done():
                res1 = await t1
            else:
                res1 = t1.result()
            cat1, auth_ok1 = classify_worker_result(res1)
            cats.append(cat1)
            acc_shared["auth_ok"] = auth_ok1 if acc_shared["auth_ok"] is None else acc_shared["auth_ok"]
        except Exception as e:
            print(f"[PAIR] Ошибка при ожидании первого воркера: {e}")
            cats.append("error")

        # Собираем результаты Kolesa
        if t2:
            # Если уже на Krisha случился бан/лимит — выставляем флаг и отменяем Kolesa
            if ("ban" in cats or acc_shared.get("banned")) and pair_cancel_on_ban and not t2.done():
                acc_shared["banned"] = True
                acc_shared["ban_reason"] = cats[0] if cats else "ban"
                print(f"[WORKER] krisha установил флаг бана для {username}")
                t2.cancel()
            
            try:
                if not t2.done():
                    res2 = await t2
                else:
                    res2 = t2.result()
                cat2, auth_ok2 = classify_worker_result(res2)
                cats.append(cat2)
                # Если первая авторизация не удалась, но вторая прошла - сохраняем успех
                if auth_ok1 is False and auth_ok2 is True:
                    acc_shared["auth_ok"] = True
            except asyncio.CancelledError:
                print(f"[PAIR] Второй воркер был отменен")
                cats.append("cancelled")
            except Exception as e:
                print(f"[PAIR] Ошибка при ожидании второго воркера: {e}")
                cats.append("error")

        # Обработка аккаунта по результатам обоих воркеров
        if acc:
            in_pool = any(a[0] == acc[0] for a in account_pool._accounts)
            # Если хотя бы один воркер сообщил о бане - удаляем аккаунт
            if "ban" in cats or acc_shared.get("banned"):
                if in_pool:
                    _delete_fp(username, "krisha", "kolesa", settings.get("sync_device_cross_platform", True))
                    await account_pool.ban(acc)
                    print(f"[PAIR] Аккаунт {username} удален из пула (причина: {acc_shared.get('ban_reason', 'ban')})")
            # Если оба завершились с ошибкой прокси - возвращаем аккаунт в пул
            elif all(c == "proxy" for c in cats if c):
                if in_pool:
                    await account_pool.release(acc)
                    print(f"[PAIR] Аккаунт {username} возвращен в пул (проблемы с прокси)")
            # В остальных случаях тоже возвращаем аккаунт в пул
            else:
                if in_pool:
                    await account_pool.release(acc)
                    print(f"[PAIR] Аккаунт {username} возвращен в пул (успешное завершение)")

    # Подготовка распределения для пар K/O
    pair_count = 0
    if paired_active:
        s_krisha = get_platform_settings("krisha")
        s_kolesa = get_platform_settings("kolesa")
        cats_krisha = s_krisha.get("categories", []) or []
        cats_kolesa = s_kolesa.get("categories", []) or []

        def _extract(p_settings):
            try:
                bc = int(p_settings.get("browser_count", 1) or 1)
            except Exception:
                bc = 1
            try:
                mppa = int(p_settings.get("max_proxies_per_account") or 1)
            except Exception:
                mppa = 1
            return bc, mppa

        bc_k, mppa_k = _extract(s_krisha)
        bc_o, mppa_o = _extract(s_kolesa)

        proxies = get_proxies()
        proxies_available = len(proxies) if (proxies and not without_proxy) else 0
        max_pairs_by_proxies = proxies_available * min(mppa_k, mppa_o) if not without_proxy else float('inf')

        accounts_available = len(account_pool._accounts) if not without_accounts else float('inf')

        pair_count = min(
            bc_k, bc_o,
            accounts_available if not without_accounts else max(bc_k, bc_o),
            max_pairs_by_proxies if not without_proxy else (accounts_available if not without_accounts else max(bc_k, bc_o)),
            len(cats_krisha) if cats_krisha else max(bc_k, bc_o),
            len(cats_kolesa) if cats_kolesa else max(bc_k, bc_o),
        )

        cats_for_k = distribute_categories(cats_krisha, pair_count) if cats_krisha else [[] for _ in range(pair_count)]
        cats_for_o = distribute_categories(cats_kolesa, pair_count) if cats_kolesa else [[] for _ in range(pair_count)]

        proxy_rows = []
        if proxies and not without_proxy:
            for _ in range(min(mppa_k, mppa_o)):
                proxy_rows.extend(proxies)

        # Счётчик для Lalafo (берём следующий cookie-спек при каждом i)
        lalafo_idx = 0

        # ГЛАВНЫЙ ПОСЛЕДОВАТЕЛЬНЫЙ ЦИКЛ СТАРТА: K_i -> O_i -> L_i
        for i in range(pair_count):
            # Берём аккаунт под пару
            acc = None
            if not without_accounts:
                acc = await account_pool.take()
                if not acc:
                    break

            # Прокси по индексу
            proxy_conf = None
            proxy_disp = None
            proxy_requests_url = None
            if not without_proxy and proxies:
                if i < len(proxy_rows):
                    proxy_row = proxy_rows[i]
                    proxy_conf = build_playwright_proxy_from_row(proxy_row)
                    proxy_disp = proxy_display_from_row(proxy_row)
                    proxy_requests_url = build_proxy_url_for_requests(proxy_row)
                else:
                    if acc and not without_accounts:
                        await account_pool.release(acc)
                    break

            # Подготавливаем девайс/UA/контекст для пары
            username = acc[1] if acc else None
            fp_key = (f"shared:{username}" if (sync_devices and username and not without_accounts) else
                      (f"krisha:{username}" if (username and not without_accounts) else None))

            ua, viewport, context_overrides, stealth_js = await build_fp_and_context_for_account(
                account_key=fp_key,
                settings=settings,
                fp_allocator=fp_allocator,
                proxy_requests_url=proxy_requests_url if (proxy_requests_url and not without_proxy) else None,
                persist_fingerprint=not without_accounts
            )

            # Копии настроек + текстовая ротация
            s_k = {**s_krisha, "text_rotation": settings.get("text_rotation", False)}
            s_o = {**s_kolesa, "text_rotation": settings.get("text_rotation", False)}
            c_k = cats_for_k[i]
            c_o = cats_for_o[i]

            # Событие: когда решено судьба запуска второй (O_i запущена или пропущена из-за мгновенного бана)
            started_second_event = asyncio.Event()

            # Запускаем оркестратор пары — ОН НЕ БЛОКИРУЕТ цикл (фоновая задача)
            pair_task = asyncio.create_task(orchestrate_pair(
                acc=acc,
                proxy_conf=proxy_conf,
                proxy_disp=proxy_disp,
                s_k=s_k,
                s_o=s_o,
                c_k=c_k,
                c_o=c_o,
                user_agent=ua,
                viewport=viewport,
                context_overrides=context_overrides,
                stealth_js=stealth_js,
                started_second_event=started_second_event,
            ))
            tasks.append(pair_task)

            # ВАЖНО: ждём только сигнал «вторая запущена или пропущена» — это обеспечивает последовательность стартов
            await started_second_event.wait()

            # Сразу после пары — пробуем запустить один Lalafo (если есть очередь)
            if lalafo_idx < len(lalafo_specs):
                spec = lalafo_specs[lalafo_idx]
                lalafo_idx += 1
                # Старт L_i и не ждём завершения (чтобы не блокировать старт следующей пары)
                t = await start_one_worker(
                    platform=spec["platform"],
                    acc=spec["acc"],
                    proxy_conf=spec["proxy"],
                    proxy_disp=spec["proxy_disp"],
                    settings_=spec["settings"],
                    categories_=spec["categories"],
                    user_agent=spec["user_agent"],
                    viewport=spec["viewport"],
                    context_overrides=spec["context_overrides"],
                    stealth_js=spec["stealth_js"],
                    manage_account=True,
                )
                tasks.append(t)

            # Небольшая пауза между i и i+1, если задана
            if rr_delay and rr_delay > 0:
                await asyncio.sleep(rr_delay)
    
    else:
        # НЕЗАВИСИМЫЙ ПОСЛЕДОВАТЕЛЬНЫЙ ЗАПУСК
        # Чередуем запуск независимых krisha/kolesa с lalafo
        lalafo_idx = 0
        independent_idx = 0
        total_to_start = len(independent_specs) + len(lalafo_specs)
        
        for i in range(total_to_start):
            # Чередуем: сначала krisha/kolesa, потом lalafo
            if independent_idx < len(independent_specs):
                spec = independent_specs[independent_idx]
                independent_idx += 1
                
                t = await start_one_worker(
                    platform=spec["platform"],
                    acc=spec["acc"],
                    proxy_conf=spec["proxy"],
                    proxy_disp=spec["proxy_disp"],
                    settings_=spec["settings"],
                    categories_=spec["categories"],
                    user_agent=spec["user_agent"],
                    viewport=spec["viewport"],
                    context_overrides=spec["context_overrides"],
                    stealth_js=spec["stealth_js"],
                    manage_account=True,
                )
                tasks.append(t)
                
            # После каждого krisha/kolesa запускаем lalafo если есть
            if lalafo_idx < len(lalafo_specs):
                spec = lalafo_specs[lalafo_idx]
                lalafo_idx += 1
                
                t = await start_one_worker(
                    platform=spec["platform"],
                    acc=spec["acc"],
                    proxy_conf=spec["proxy"],
                    proxy_disp=spec["proxy_disp"],
                    settings_=spec["settings"],
                    categories_=spec["categories"],
                    user_agent=spec["user_agent"],
                    viewport=spec["viewport"],
                    context_overrides=spec["context_overrides"],
                    stealth_js=spec["stealth_js"],
                    manage_account=True,
                )
                tasks.append(t)
                
            if rr_delay and rr_delay > 0:
                await asyncio.sleep(rr_delay)

    if has_callback:
        await callback.answer("✅ Рассылка запущена!")
    else:
        await bot.send_message(chat_id, "✅ Рассылка запущена (последовательный запуск)")

    set_last_mailing_end()


async def run_worker(
    bot: Bot,
    chat_id: int,
    message_id: int,
    platform: str,
    acc,
    account_pool: AccountPool,
    proxy: dict | None = None,
    headless: bool = True,
    platform_settings: dict = None,
    categories=None,
    cookie_data=None,
    user_agent: str | None = None,
    viewport: dict | None = None,
    context_overrides: dict | None = None,
    stealth_js: str | None = None,
    manage_account: bool = True,
    acc_shared: Optional[Dict[str, Any]] = None,
):
    # Проверка на бан от другого воркера
    if acc_shared and acc_shared.get("banned"):
        log_lines = [
            f"<b>Платформа:</b> <code>{platform}</code>",
            f"<b>Аккаунт:</b> <code>{acc[1] if acc else 'Без аккаунта'}</code>",
            f"<b>Прокси:</b> <code>{proxy.get('server') if proxy else 'Без прокси'}</code>",
            f"<b>Категории:</b>\n<code>{chr(10).join(categories) if categories else 'Нет'}</code>",
            f"Статус: 🚫 Аккаунт забанен другим воркером: {acc_shared.get('ban_reason', 'ban')}"
        ]
        await update_worker_log(bot, chat_id, message_id, log_lines)
        return {"status": "other_worker_banned"}

    global BROWSER_COUNTER
    browser_id = BROWSER_COUNTER
    BROWSER_COUNTER += 1
    username = acc[1] if acc else "Без аккаунта"
    password = acc[2] if acc and len(acc) > 2 else ""

    if categories is None:
        categories = []
    elif not isinstance(categories, list):
        categories = [categories]

    proxy_disp = (proxy or {}).get("server") if proxy else None

    log_lines = [
        f"<b>Платформа:</b> <code>{platform}</code>",
        f"<b>Аккаунт:</b> <code>{username}</code>",
        f"<b>Прокси:</b> <code>{proxy_disp or 'Без прокси'}</code>",
        f"<b>Категории:</b>\n<code>{chr(10).join(categories) if categories else 'Нет'}</code>"
    ]

    def log(msg):
        log_lines.append(f"Статус: {msg}")

    ACTIVE_BROWSERS[browser_id] = {
        "chat_id": chat_id,
        "message_id": message_id,
        "log_lines": log_lines.copy(),
        "status": "running",
        "platform": platform,
        "username": username,
        "proxy": proxy_disp,
        "bot": bot,
        "task": None,
    }

    await update_browser_message(bot, browser_id)

    log("🕒 Запуск воркера...")
    await update_worker_log(bot, chat_id, message_id, log_lines)

    # Импортируем соответствующий модуль для работы с платформой
    try:
        if platform == "krisha":
            from playwright_scripts.krisha_worker import run_krisha as run_platform_worker
        elif platform == "kolesa":
            from playwright_scripts.kolesa_worker import run_kolesa as run_platform_worker
        elif platform == "lalafo":
            from playwright_scripts.lalafo_worker import run_lalafo as run_platform_worker
        else:
            raise ValueError(f"Неизвестная платформа {platform}")
    except Exception as e:
        log(f"❌ Не удалось импортировать модуль: {e}")
        ACTIVE_BROWSERS.pop(browser_id, None)
        if acc and platform != "lalafo" and manage_account:
            await account_pool.ban(acc)
        return {"status": "import_error"}

    # Подготовка параметров для запуска воркера
    worker_kwargs = dict(
        proxy=proxy,
        username=username,
        password=password,
        headless=headless,
        bot_token=bot.token,
        chat_id=chat_id,
        message_id=message_id,
        platform_settings=platform_settings,
        categories=categories,
        user_agent=user_agent,
        viewport=viewport,
        context_overrides=context_overrides,
        stealth_js=stealth_js,
        acc_shared=acc_shared,
    )
    
    if platform == "lalafo":
        worker_kwargs["cookie_data"] = cookie_data or (platform_settings.get("cookie_data") if platform_settings else None)

    # Проверяем, поддерживает ли воркер параметр stealth_js
    try:
        params = inspect.signature(run_platform_worker).parameters
        if "stealth_js" not in params:
            worker_kwargs.pop("stealth_js", None)
        # Проверяем поддержку acc_shared
        if "acc_shared" not in params:
            worker_kwargs.pop("acc_shared", None)
    except Exception:
        worker_kwargs.pop("stealth_js", None)
        worker_kwargs.pop("acc_shared", None)

    # Запускаем воркер как асинхронную задачу
    task = asyncio.create_task(run_platform_worker(**worker_kwargs))
    ACTIVE_BROWSERS[browser_id]["task"] = task

    try:
        result = await task
        category, auth_ok = classify_worker_result(result)
        
        # ВАЖНО: Добавляем логирование для отладки
        print(f"[WORKER RESULT] Platform: {platform}, Username: {username}, Result: {result}, Category: {category}")
        
        # Обновляем общее состояние аккаунта
        if acc_shared is not None:
            if category == "ban" or result is False:  # ВАЖНО: проверяем и False напрямую
                acc_shared["banned"] = True
                acc_shared["ban_reason"] = f"{platform}:{category}"
                print(f"[WORKER] {platform} установил флаг бана для {username}")
            
            # Сохраняем результат авторизации
            if auth_ok is not None:
                acc_shared["auth_ok"] = auth_ok

        # ИСПРАВЛЕНИЕ: Обрабатываем результат для ВСЕХ платформ
        if manage_account and acc:
            # ВАЖНО: Сначала проверяем прямые результаты False/True от воркеров
            if result is False:
                # False от воркера ВСЕГДА означает ограничение/бан
                category = "ban"
                print(f"[WORKER] Получен False от {platform} для {username} - помечаем как ban")
            elif result is True:
                # True означает успех
                category = "success"
            # Затем проверяем строковые результаты
            elif result in ["invalid_credentials", "account_blocked", "account_restricted", "restricted", "session_lost"]:
                category = "ban"
            elif result == "proxy_error":
                category = "proxy"
            elif isinstance(result, dict):
                status = result.get("status", "")
                # Для словарей тоже проверяем статусы
                if status in ["other_worker_banned", "invalid_credentials", "account_blocked", "account_restricted", "banned"]:
                    category = "ban"
                elif status == "proxy_error":
                    category = "proxy"
                # Проверяем auth_ok в словаре
                elif result.get("auth_ok") is False:
                    category = "ban"
            
            # Обработка в зависимости от категории
            if category == "proxy":
                log("❌ Ошибка прокси/сети — аккаунт возвращён в пул.")
                await account_pool.release(acc)
                print(f"[WORKER] Аккаунт {username} возвращен в пул (proxy error)")
                
            elif category == "ban":
                # Определяем причину бана для лога
                ban_reason = "ограничение/бан"
                if result is False:
                    ban_reason = "ограничение отправки сообщений (вернул False)"
                elif result == "invalid_credentials":
                    ban_reason = "невалидные учетные данные"
                elif result == "account_blocked":
                    ban_reason = "аккаунт заблокирован"
                elif result == "session_lost":
                    ban_reason = "потеря сессии"
                elif result in ["account_restricted", "restricted"]:
                    ban_reason = "ограничение аккаунта"
                    
                log(f"❌ {ban_reason} — аккаунт удалён из пула.")
                
                # Очищаем fingerprints
                try:
                    if username and username != "Без аккаунта":
                        # Очищаем все возможные fingerprints
                        ua_store.delete_fingerprint(f"{platform}:{username}")
                        ua_store.delete_fingerprint(f"shared:{username}")
                        if platform == "krisha":
                            ua_store.delete_fingerprint(f"kolesa:{username}")
                        elif platform == "kolesa":
                            ua_store.delete_fingerprint(f"krisha:{username}")
                except Exception as e:
                    print(f"[UA_STORE] FP cleanup error: {e}")
                
                # ВАЖНО: Удаляем аккаунт из пула
                await account_pool.ban(acc)
                print(f"[WORKER] ✅ Аккаунт {username} УДАЛЕН из пула (платформа: {platform}, причина: {ban_reason})")
                
            else:
                log("✅ Завершено — аккаунт возвращён в пул.")
                await account_pool.release(acc)
                print(f"[WORKER] Аккаунт {username} возвращен в пул (success)")
                
        elif platform == "lalafo":
            # Для lalafo оставляем как было
            if category == "proxy":
                log("❌ Ошибка прокси/сети.")
            elif category == "ban":
                log("❌ Невалид/бан/ограничение.")
            else:
                log("✅ Завершено.")
        else:
            # Для случаев без управления аккаунтом (парный режим)
            if category == "proxy":
                log("❌ Ошибка прокси/сети.")
            elif category == "ban" or result is False:
                log("❌ Невалид/бан/ограничение.")
            else:
                log("✅ Завершено.")
                
    except Exception as e:
        # Обрабатываем исключения при выполнении воркера
        log(f"❌ Ошибка выполнения: {e}")
        if manage_account and acc and platform != "lalafo":
            el = str(e).lower()
            if any(k in el for k in ["proxy", "network", "timeout"]):
                await account_pool.release(acc)
                print(f"[WORKER] Аккаунт {username} возвращен в пул (сетевая ошибка: {e})")
            else:
                # При любой другой ошибке удаляем аккаунт
                try:
                    if username and username != "Без аккаунта":
                        ua_store.delete_fingerprint(f"{platform}:{username}")
                        ua_store.delete_fingerprint(f"shared:{username}")
                        if platform == "krisha":
                            ua_store.delete_fingerprint(f"kolesa:{username}")
                        elif platform == "kolesa":
                            ua_store.delete_fingerprint(f"krisha:{username}")
                except Exception as del_e:
                    print(f"[UA_STORE] Ошибка очистки отпечатка: {del_e}")
                await account_pool.ban(acc)
                print(f"[WORKER] Аккаунт {username} удален из пула при ошибке (платформа: {platform}, ошибка: {e})")

    # Удаляем информацию о браузере по завершении
    ACTIVE_BROWSERS.pop(browser_id, None)
    return result


@router.message(F.text == "/start")
async def cmd_start(message: types.Message, state: FSMContext = None):
    if state:
        await state.clear()

    gif_url = "https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3am5zcnU1cTgyeDNpOWlydGp4dTMwcmF2enNzdWk5ZHg1ZzRoZ2M5ZiZlcD12MV9naWZzX3JlbGF0ZWQmY3Q9Zw/3o7qDPOeDdG9QkEdt6/giphy.gif"
    try:
        await message.answer_animation(animation=gif_url)
    except Exception as e:
        print(f"[ERROR] Не удалось отправить гифку: {e}")

    stats = get_stats()
    blacklisted_count = get_blacklisted_seller_count()

    user_id = message.from_user.id
    first_name = message.from_user.first_name or "Пользователь"
    username = message.from_user.username
    save_user(user_id, first_name, username)
    user = get_user(user_id)
    stats = get_stats()

    first_login = user["first_login"]
    try:
        from datetime import datetime
        first_login = datetime.strptime(first_login, "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y")
    except Exception:
        pass

    last_mailing = stats["last_mailing_start"] or "никогда"
    if last_mailing != "никогда":
        try:
            last_mailing = datetime.strptime(last_mailing, "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y %H:%M")
        except Exception:
            pass

    total_browsers = len(ACTIVE_BROWSERS)
    platforms_running = {data["platform"].upper() for data in ACTIVE_BROWSERS.values()}

    welcome_text = (
        f"✨ <b>Добро пожаловать, {html.escape(first_name)}!</b>\n\n"
        f"👤 <b>Пользователь:</b> {f'@{html.escape(username)}' if username else 'не указан'}\n"
        f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
        f"📅 <b>Впервые с нами:</b> {user['first_login']}\n"
        f"📊 <b>Всего сообщений отправлено:</b> <code>{stats['total_messages_sent']:,}</code>\n"
        f"🕒 <b>Последняя рассылка:</b> {last_mailing}\n\n"
        f"🚫 <b>В чёрном списке продавцов:</b> <code>{blacklisted_count}</code>\n\n"
    )

    if total_browsers > 0:
        welcome_text += (
            f"🚀 <b>Сейчас запущено:</b> <code>{total_browsers}</code> браузеров\n"
            f"🔗 <b>На платформах:</b> {' | '.join(f'<code>{p}</code>' for p in platforms_running)}\n\n"
        )
    else:
        welcome_text += "🟢 <b>Система готова к работе!</b>\n\n"

    welcome_text += (
        f"🔧 <b>Возможности бота:</b>\n"
        f"• 📬 Отправка сообщений на <code>krisha.kz</code>, <code>kolesa.kz</code> и <code>lalafo.kg</code>\n"
        f"• 🛠️ Контроль браузеров\n"
        f"• 📊 Анти-дубли и статистика\n"
        f"• 🔐 Хранение аккаунтов и прокси\n\n"
        f"👇 Выбери действие:"
    )

    await message.answer(welcome_text, parse_mode="HTML", reply_markup=get_main_menu())


@router.callback_query(F.data == "proxy")
async def proxy(callback: types.CallbackQuery):
    await proxy_menu(callback)


@router.callback_query(F.data == "start_mailing")
async def start_mailing(callback: types.CallbackQuery, bot: Bot):
    chat_id = callback.message.chat.id if callback.message else None
    await start_mailing_core(bot, chat_id, callback=callback)


async def auto_start_mailing(bot: Bot):
    global AUTO_START_TASK
    while True:
        settings = get_settings()
        timer = settings.get("autostart_timer")
        if not timer or timer <= 0:
            break
        await asyncio.sleep(timer)
        # Закрываем все браузеры перед автозапуском
        try:
            await close_all_browsers_force(bot)
        except Exception as e:
            print(f"[AUTO START] Ошибка при закрытии браузеров: {e}")
        
        settings = get_settings()
        timer = settings.get("autostart_timer")
        if not timer or timer <= 0:
            break
        
        chat_id = None
        if ACTIVE_BROWSERS:
            for browser_data in ACTIVE_BROWSERS.values():
                chat_id = browser_data.get("chat_id")
                if chat_id:
                    break
        
        if not chat_id:
            try:
                from config import ADMIN_IDS
                if ADMIN_IDS:
                    chat_id = ADMIN_IDS[0]
            except ImportError:
                chat_id = None
        
        if chat_id:
            try:
                await start_mailing_core(bot, chat_id)
            except Exception as e:
                print(f"[AUTO START] Ошибка: {e}")
    
    AUTO_START_TASK = None


async def restart_auto_start_timer(bot: Bot):
    global AUTO_START_TASK
    if AUTO_START_TASK and not AUTO_START_TASK.done():
        AUTO_START_TASK.cancel()
        try:
            await AUTO_START_TASK
        except asyncio.CancelledError:
            pass
    
    settings = get_settings()
    timer = settings.get("autostart_timer")
    if timer and timer > 0:
        AUTO_START_TASK = asyncio.create_task(auto_start_mailing(bot))
    else:
        AUTO_START_TASK = None


@router.callback_query(F.data == "manage_browsers")
async def manage_browsers(callback: types.CallbackQuery):
    await callback.answer()
    if not ACTIVE_BROWSERS:
        text = "📭 Нет запущенных браузеров"
        kb = get_manage_browsers_keyboard(has_browsers=False)
    else:
        text = "🟢 <b>Запущенные браузеры:</b>\n\n"
        for bid, data in ACTIVE_BROWSERS.items():
            status = "⏸️ Приостановлен" if data["status"] == "paused" else "▶️ Работает"
            username_display = data['username'] if data['username'] else "Без аккаунта"
            text += (
                f"📌 <b>#{bid}</b> | {data['platform'].upper()} | {username_display}\n"
                f"🔹 Статус: {status}\n"
                f"🔹 Прокси: {data['proxy'] or 'Без прокси'}\n\n"
            )
        kb = get_manage_browsers_list_keyboard(ACTIVE_BROWSERS)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data == "work_platforms")
async def work_platforms(callback: types.CallbackQuery):
    await callback.answer()
    await platforms_menu(callback)


@router.callback_query(F.data == "settings")
async def settings(callback: types.CallbackQuery):
    await show_settings(callback)


@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await callback.message.edit_text(
        "Добро пожаловать! Выберите действие:",
        reply_markup=get_main_menu()
    )


# Обработчики для управления браузерами с новой клавиатурой
@router.callback_query(F.data.startswith("pause_browser_id:"))
async def pause_browser_by_id(callback: types.CallbackQuery):
    browser_id = int(callback.data.split(":")[1])
    if browser_id in ACTIVE_BROWSERS:
        ACTIVE_BROWSERS[browser_id]["status"] = "paused"
        await callback.answer("⏸️ Браузер приостановлен")
        await manage_browsers(callback)
    else:
        await callback.answer("❌ Браузер не найден", show_alert=True)


@router.callback_query(F.data.startswith("resume_browser_id:"))
async def resume_browser_by_id(callback: types.CallbackQuery):
    browser_id = int(callback.data.split(":")[1])
    if browser_id in ACTIVE_BROWSERS:
        ACTIVE_BROWSERS[browser_id]["status"] = "running"
        await callback.answer("▶️ Браузер продолжает работу")
        await manage_browsers(callback)
    else:
        await callback.answer("❌ Браузер не найден", show_alert=True)


@router.callback_query(F.data.startswith("close_browser_id:"))
async def close_browser_by_id(callback: types.CallbackQuery):
    browser_id = int(callback.data.split(":")[1])
    if browser_id in ACTIVE_BROWSERS:
        data = ACTIVE_BROWSERS[browser_id]
        if data["task"]:
            data["task"].cancel()
        ACTIVE_BROWSERS.pop(browser_id, None)
        await callback.answer("✅ Браузер закрыт")
        await manage_browsers(callback)
    else:
        await callback.answer("❌ Браузер не найден", show_alert=True)


# Старые обработчики для совместимости
@router.callback_query(F.data == "pause_browser")
async def pause_browser(callback: types.CallbackQuery):
    for bid, data in ACTIVE_BROWSERS.items():
        if data["message_id"] == callback.message.message_id:
            data["status"] = "paused"
            await update_browser_message(callback.bot, bid)
            await callback.answer("⏸️ Браузер приостановлен")
            break


@router.callback_query(F.data == "resume_browser")
async def resume_browser(callback: types.CallbackQuery):
    for bid, data in ACTIVE_BROWSERS.items():
        if data["message_id"] == callback.message.message_id:
            data["status"] = "running"
            await update_browser_message(callback.bot, bid)
            await callback.answer("▶️ Браузер продолжает работу")
            break


@router.callback_query(F.data == "close_browser")
async def close_browser(callback: types.CallbackQuery):
    for bid, data in ACTIVE_BROWSERS.copy().items():
        if data["message_id"] == callback.message.message_id:
            if data["task"]:
                data["task"].cancel()
            ACTIVE_BROWSERS.pop(bid, None)
            await callback.answer("✅ Браузер закрыт")
            await callback.message.edit_text("❌ Браузер закрыт", reply_markup=get_back_menu())
            break


@router.callback_query(F.data == "close_all_browsers")
async def close_all_browsers(callback: types.CallbackQuery):
    for bid, data in ACTIVE_BROWSERS.copy().items():
        if data["task"]:
            data["task"].cancel()
    ACTIVE_BROWSERS.clear()
    await callback.answer("🛑 Все браузеры закрыты")
    await callback.message.edit_text(
        "📭 Нет запущенных браузеров",
        reply_markup=get_manage_browsers_keyboard(has_browsers=False)
    )


@router.callback_query(F.data == "noop")
async def noop_handler(callback: types.CallbackQuery):
    """Обработчик для кнопок без действия (заголовки браузеров)"""
    await callback.answer()