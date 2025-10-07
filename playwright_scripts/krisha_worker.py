import asyncio
import argparse
import html
from urllib.parse import urlparse
from playwright.async_api import async_playwright
from datetime import datetime, timedelta
import re
import requests
import random
import time
import json
import aiohttp  
from collections import deque
from typing import Optional
from playwright_scripts.utils import replace_placeholders, extract_price
from db import is_ad_sent, add_sent_ad, add_blacklisted_seller, is_seller_blacklisted, increment_message_count
from utils.global_throttler import global_throttle
from utils.anti_profile import add_stealth_scripts
from utils.account_status_manager import account_manager
from utils.api_manager import APIManager  # ← ДОБАВИТЬ

MONTHS_RU = {
    'янв': 1, 'фев': 2, 'мар': 3, 'апр': 4, 'май': 5, 'июн': 6,
    'июл': 7, 'авг': 8, 'сен': 9, 'окт': 10, 'ноя': 11, 'дек': 12
}
# Создаем API Manager (без немедленной загрузки настроек)
try:
    api_manager = APIManager()
except Exception as e:
    print(f"[INIT] Ошибка создания APIManager: {e}")
    api_manager = None
# --- ПОВЕДЕНИЕ И УСТОЙЧИВОСТЬ ---
MAX_PAGES_PER_CATEGORY = 15
PRE_MESSAGE_DELAY_SEC = (4.5, 6.0)
CHAT_READY_DELAY_SEC = (4.5, 6.0)
PASTE_BEFORE_SEND_DELAY_SEC = (1.8, 6.8)
POST_SEND_SETTLE_DELAY_SEC = (1.2, 2.4)
BETWEEN_MESSAGES_DELAY_SEC = (4.0, 7.0)
BETWEEN_PAGES_DELAY_SEC = (1.5, 3.5)
GOTO_RETRY_ATTEMPTS = 3
GOTO_TIMEOUT_MS = 20000
VERIFY_SENT_TIMEOUT_SEC = 7.0
VERIFY_SENT_FIRST_PHASE_SEC = 3.0
# Интервал проверки бана аккаунта в других воркерах
ACCOUNT_STATUS_CHECK_INTERVAL_SEC = 10

PROXY_ERROR_KEYWORDS = [
    "proxy", "network", "connection", "timeout", "econnrefused",
    "could not reach", "err_proxy_connection_failed",
    "err_connection_timed_out", "net::err_proxy_connection_failed",
    "browser closed", "page.goto: timeout",
    "target page, context or browser has been closed",
    "navigation timeout",
    "err_tunnel_connection_failed",
    "err_timed_out",
    "err_aborted",
    "chrome-error://",
]

def pick_custom_text(custom_text):
    if isinstance(custom_text, list) and custom_text:
        return random.choice(custom_text)
    elif isinstance(custom_text, str):
        return custom_text
    return ""

# ============ УТИЛИТЫ ============

def edit_log(bot_token, chat_id, message_id, text: str):
    url = f"https://api.telegram.org/bot{bot_token}/editMessageText"
    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML",
    }
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(f"[LOG ERROR] Failed to edit message via API: {e}")

def _proxy_disp(proxy) -> str | None:
    if not proxy:
        return None
    if isinstance(proxy, dict):
        return proxy.get("server")
    try:
        p = urlparse(proxy)
        if p.scheme and p.hostname and p.port:
            return f"{p.scheme}://{p.hostname}:{p.port}"
    except Exception:
        pass
    return str(proxy)

def parse_krisha_date(date_str):
    date_str = date_str.strip().lower()
    now = datetime.now()
    if date_str.startswith("сегодня"):
        return now.date()
    if date_str.startswith("вчера"):
        return (now - timedelta(days=1)).date()
    m = re.match(r"(\d{1,2})\s+([а-я]+)\.?", date_str)
    if m:
        day, mon = int(m.group(1)), MONTHS_RU.get(m.group(2)[:3])
        if mon:
            return datetime(now.year, mon, day).date()
    return None

async def get_seller_id(tab):
    try:
        seller_id = await tab.evaluate("window.digitalData?.product?.seller?.id")
        if seller_id:
            return str(seller_id)
    except Exception:
        pass
    return None

async def check_account_restriction(page):
    try:
        user_info_elements = await page.query_selector_all('div.mes-user-info__primary')
        for element in user_info_elements:
            text_content = await element.text_content()
            if text_content and "Пользователь приложения" in text_content:
                return True
        return False
    except Exception:
        return False

async def login_krisha(page, username, password):
    await page.goto("https://krisha.kz", wait_until="domcontentloaded", timeout=45000)

    cabinet_link = page.locator("a.cabinet-link", has_text="Личный кабинет")
    await cabinet_link.wait_for(state="visible")
    await cabinet_link.click()

    await page.wait_for_selector("input#login", state="visible")
    login_input = page.locator("input#login")
    await login_input.click()
    await login_input.fill("")
    await login_input.type(username, delay=120)

    try:
        continue_btn = page.locator("button.ui-button--blue")
        await continue_btn.wait_for(state="visible")
        await continue_btn.click()
    except Exception:
        try:
            await page.keyboard.press("Enter")
        except Exception:
            pass

    try:
        await page.wait_for_timeout(1500)
        alerts = await page.query_selector_all(".alert.alert-danger")
        for alert in alerts:
            error_text = await alert.inner_text()
            if error_text:
                if "учетная запись заблокирована" in error_text.lower():
                    return "account_blocked"
                if "Неверно указан логин или пароль" in error_text or "Неверный логин или пароль" in error_text:
                    return "invalid_credentials"
    except Exception:
        pass

    try:
        await page.wait_for_selector("input#password", state="visible", timeout=4000)
    except Exception:
        pass

    password_input = page.locator("input#password")
    await password_input.click()
    await password_input.fill("")
    await password_input.type(password, delay=120)
    try:
        await page.keyboard.press("Enter")
    except Exception:
        try:
            await page.click("button.ui-button--blue")
        except Exception:
            pass

    try:
        await page.wait_for_timeout(1000)
        alerts = await page.query_selector_all("div.alert.alert-danger")
        for alert in alerts:
            error_text = await alert.inner_text()
            if error_text:
                err = " ".join(error_text.split()).lower()
                if "учетная запись заблокирована" in err:
                    return "account_blocked"
                if ("неверно указан логин или пароль" in err
                    or "неверный логин или пароль" in err):
                    return "invalid_credentials"
    except Exception:
        pass

    try:
        await page.wait_for_selector("ul.navbar-menu", state="visible", timeout=5000)
        return "success"
    except Exception:
        return "auth_failed"

def _coerce_playwright_proxy(p) -> dict | None:
    if not p:
        return None
    if isinstance(p, dict) and "server" in p:
        return p
    if isinstance(p, str):
        pr = urlparse(p)
        if pr.scheme and pr.hostname and pr.port:
            conf = {"server": f"{pr.scheme}://{pr.hostname}:{pr.port}"}
            if pr.username and pr.password:
                conf["username"] = pr.username
                conf["password"] = pr.password
            return conf
        return {"server": p}
    return None

def _is_proxy_or_network_error(msg: str) -> bool:
    low = (msg or "").lower()
    return any(k in low for k in PROXY_ERROR_KEYWORDS)

def _is_chrome_error_url(url: str) -> bool:
    return isinstance(url, str) and url.startswith("chrome-error://")

def _sec(val) -> float:
    if isinstance(val, (tuple, list)) and len(val) == 2:
        return float(random.uniform(val[0], val[1]))
    return float(val)

async def _pause(seconds):
    await asyncio.sleep(_sec(seconds))

async def navigate_with_retries(page, url: str, wait_until: str = "domcontentloaded", timeout_ms: int = GOTO_TIMEOUT_MS, attempts: int = GOTO_RETRY_ATTEMPTS):
    last_err = None
    for i in range(1, attempts + 1):
        try:
            resp = await page.goto(url, wait_until=wait_until, timeout=timeout_ms)
            if _is_chrome_error_url(page.url):
                raise RuntimeError(f"Navigated to chrome-error page: {page.url}")
            return resp
        except Exception as e:
            last_err = e
            if "Target page, context or browser has been closed" in str(e):
                raise
            await asyncio.sleep(1.5 * i)
            try:
                await page.goto("about:blank", wait_until="domcontentloaded", timeout=timeout_ms)
            except Exception:
                pass
    raise last_err

def normalize_message_text(text: str) -> str:
    return (text or "").strip()

async def confirm_message_sent(page, input_selector: str, expected_text: str, timeout_sec: float = VERIFY_SENT_TIMEOUT_SEC) -> tuple[bool, str]:
    end_time = time.monotonic() + timeout_sec
    first_phase_end = time.monotonic() + VERIFY_SENT_FIRST_PHASE_SEC
    expected_norm = expected_text.lower()

    sels = [
        '.mes__messages .mes-message--my',
        '.mes__messages .message--my',
        '.mes-message._my',
        '.message._my',
        '.mes-message--out',
        '.message-out',
        '.mes-message.my',
        '.message.my',
    ]

    async def has_bubble_with_text() -> bool:
        try:
            return await page.evaluate("""(selectors, expected) => {
                const norm = s => (s || '').replace(/\s+/g,' ').trim().toLowerCase();
                const exp = norm(expected);
                for (const sel of selectors) {
                  const nodes = document.querySelectorAll(sel);
                  for (const node of nodes) {
                    const t = norm(node.textContent || '');
                    if (t.includes(exp)) return true;
                  }
                }
                return false;
            }""", sels, expected_norm)
        except Exception:
            return False

    async def input_is_cleared() -> bool:
        try:
            return await page.evaluate("""(sel) => {
                const el = document.querySelector(sel);
                if (!el) return false;
                const text = (el.innerText || '').replace(/\s+/g,' ').trim();
                return text.length === 0;
            }""", input_selector)
        except Exception:
            return False

    while time.monotonic() < first_phase_end:
        if await has_bubble_with_text():
            return True, "bubble"
        await asyncio.sleep(0.3)

    while time.monotonic() < end_time:
        if await has_bubble_with_text():
            return True, "bubble"
        if await input_is_cleared():
            return True, "input_cleared"
        await asyncio.sleep(0.3)

    return False, "timeout"

# ============ НОВЫЙ КРАСИВЫЙ ЛОГГЕР ============

def _elapsed_str(dt_start: datetime) -> str:
    delta = datetime.now() - dt_start
    total = int(delta.total_seconds())
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def _progress_bar_emoji(current: int, total: int, width: int = 14) -> str:
    """
    Цветной прогресс-бар: 🟩 заполнено, ⬜ пусто.
    """
    total = max(total, 1)
    fill = max(0, min(width, int(round(width * current / total))))
    return "🟩" * fill + "⬜" * (width - fill)

def _trim_url(u: str, max_len: int = 70) -> str:
    if not u:
        return "-"
    if len(u) <= max_len:
        return u
    head = u[:max_len - 15]
    tail = u[-10:]
    return f"{head}…{tail}"

class StatusLogger:
    def __init__(self, bot_token: str, chat_id: int, message_id: int,
                 username: str, proxy, categories: list[str], max_unsubscribes: int):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.message_id = message_id

        self.username = username
        self.proxy_text = _proxy_disp(proxy) or "Без прокси"
        self.categories = list(categories or [])
        self.max_unsubscribes = max_unsubscribes

        self.ua = "-"
        self.vp = "-"
        self.is_mobile = False
        self.current_category = None
        self.sent = 0
        self.state = "Инициализация…"
        self.state_emoji = "⏳"
        self.events = deque(maxlen=5)
        self.start_time = datetime.now()

    def set_profile(self, ua: str, vp: dict | None, is_mobile: bool):
        self.ua = (ua or "-").strip()
        if len(self.ua) > 180:
            self.ua = self.ua[:180] + "…"
        if vp and isinstance(vp, dict):
            self.vp = f"{vp.get('width','-')}x{vp.get('height','-')}"
        else:
            self.vp = "-"
        self.is_mobile = bool(is_mobile)

    def set_state(self, text: str, emoji: str = "ℹ️"):
        self.state = text
        self.state_emoji = emoji

    def set_current_category(self, url: str):
        self.current_category = url

    def inc_sent(self, n: int = 1):
        self.sent += n

    def event(self, text: str):
        self.events.append(text)

    def render(self) -> str:
        device_icon = "📱" if self.is_mobile else "🖥️"
        device = f"{device_icon} {self.vp}"
        bar = _progress_bar_emoji(self.sent, self.max_unsubscribes, width=14)
        progress_line = f"✉️ {self.sent}/{self.max_unsubscribes}  {bar}"
        elapsed = _elapsed_str(self.start_time)

        lines = []
        lines.append("🤖 <b>Krisha Worker</b>")
        lines.append(f"👤 Аккаунт: <code>{html.escape(self.username)}</code>")
        lines.append(f"🛰️ Прокси: <code>{html.escape(self.proxy_text)}</code>")
        lines.append(f"🧩 Устройство: {device}")
        lines.append(f"🕸️ UA: <code>{html.escape(self.ua)}</code>")
        if self.categories:
            lines.append(f"🗂️ Категорий: <b>{len(self.categories)}</b>")
        cur = _trim_url(self.current_category or "-")
        lines.append(f"🧭 Сейчас категория: <code>{html.escape(cur)}</code>")
        lines.append(f"📌 Статус: {self.state_emoji} <b>{html.escape(self.state)}</b>")
        lines.append(progress_line)
        lines.append(f"⏱️ Время: <code>{elapsed}</code>")
        if self.events:
            lines.append("")
            lines.append("📝 Последние события:")
            for ev in list(self.events)[-5:]:
                lines.append(f"• {html.escape(ev)}")
        return "\n".join(lines)

    def push(self):
        edit_log(self.bot_token, self.chat_id, self.message_id, self.render())

# ============ ПЕРИОДИЧЕСКАЯ ПРОВЕРКА СТАТУСА АККАУНТА ============
async def check_account_status_periodically(username, worker_id, status_logger=None):
    """Периодически проверяет статус аккаунта в менеджере аккаунтов"""
    while True:
        await asyncio.sleep(ACCOUNT_STATUS_CHECK_INTERVAL_SEC)
        if not username or username == "Без аккаунта":
            continue
            
        acc_status = await account_manager.get_account_status(username)
        if acc_status and acc_status.get("banned") and acc_status.get("ban_worker_id") != worker_id:
            if status_logger:
                status_logger.set_state(f"Аккаунт забанен другим воркером: {acc_status.get('ban_reason', 'unknown')}", "🚫")
                status_logger.event(f"Остановка работы из-за бана в другом воркере")
                status_logger.push()
            return acc_status
    
    return None

# ============ ОСНОВНОЙ СЦЕНАРИЙ ============
async def run_krisha(
    proxy,
    username,
    password,
    headless,
    bot_token,
    chat_id,
    message_id,
    platform_settings=None,
    categories=None,
    user_agent: str | None = None,
    viewport: dict | None = None,
    context_overrides: dict | None = None,
    stealth_js: str | None = None,
    acc_shared=None,
    worker_id: int = None,  # Новый параметр для идентификации воркера
):

    # Инициализация API Manager с приоритетом селектора
    global api_manager
    if api_manager:
        try:
            # Загружаем settings.json для токенов и настроек
            with open("settings.json", "r", encoding="utf-8") as f:
                settings_data = json.load(f)
            
            # Передаем в load_settings (загружает токены, URLs, platform_id и т.д.)
            api_manager.load_settings(settings_data)
            
            # ВАЖНО: Проверяем селектор "Ссылка [Link]" для включения/выключения API
            has_link_selector = False
            if platform_settings:
                selectors = platform_settings.get("selectors", [])
                if isinstance(selectors, str):
                    selectors = [selectors]
                has_link_selector = "Ссылка [Link]" in selectors
            
            # Устанавливаем enabled только если селектор включен
            api_manager.enabled = has_link_selector
            
            if api_manager.enabled:
                print(f"[API Manager] ✅ API включен (platform_id: {api_manager.default_platform_id})")
            else:
                print("[API Manager] ⏸️ API отключен (селектор [Link] неактивен)")
                
        except FileNotFoundError:
            print("[API Manager] ⚠️ settings.json не найден, API отключен")
            api_manager.enabled = False
        except Exception as e:
            print(f"[API Manager] ❌ Ошибка загрузки: {e}")
            api_manager.enabled = False
    # Регистрируем воркер в менеджере аккаунтов
    if username and username != "Без аккаунта" and worker_id is not None:
        current_task = asyncio.current_task()
        acc_status = await account_manager.register_worker(worker_id, username, current_task)
        
        # Если аккаунт уже заблокирован, завершаем работу
        if acc_status["banned"]:
            return {"status": "other_worker_banned", "reason": acc_status["ban_reason"]}
    
    if acc_shared and acc_shared.get("banned"):
        return {"status": "other_worker_banned"}
    
    if categories is None:
        categories = []
    elif isinstance(categories, str):
        categories = [categories]

    custom_text = ""
    max_unsubscribes = 25
    selectors = []
    if platform_settings:
        custom_text = platform_settings.get("custom_text", "")
        try:
            max_unsubscribes = int(platform_settings.get("max_unsubscribes") or 25)
        except Exception:
            max_unsubscribes = 25         
        selectors = platform_settings.get("selectors", [])
        if isinstance(selectors, str):
            selectors = [selectors]

    parse_name = "Парс имени" in selectors
    parse_price = "Парс цены" in selectors
    parse_title = "Парс названия" in selectors

    unsubscribed = 0
    account_restricted = False

    status = StatusLogger(bot_token, chat_id, message_id, username, proxy, categories, max_unsubscribes)
    status.set_state("Авторизация…", "🔐")
    status.push()

    launch_args = {
        "headless": headless,
        "channel": "chrome",
        "args": [
            "--ignore-gpu-blocklist",
            "--enable-webgl",
            "--enable-accelerated-2d-canvas",
            "--use-gl=angle",
            "--use-angle=d3d11",
        ],
    }
    proxy_conf = _coerce_playwright_proxy(proxy)
    if proxy_conf:
        launch_args["proxy"] = proxy_conf

    MAX_PROXY_ATTEMPTS = 3
    MAX_LOGIN_ATTEMPTS = 3
    last_proxy_error_str = ""
    browser = None
    login_success = False
    
    # Запускаем периодическую проверку статуса аккаунта
    status_check_task = None
    if username and username != "Без аккаунта" and worker_id is not None:
        status_check_task = asyncio.create_task(
            check_account_status_periodically(username, worker_id, status)
        )

    try:
        async with async_playwright() as p:
            for proxy_attempt in range(1, MAX_PROXY_ATTEMPTS + 1):
                try:
                    browser = await p.chromium.launch(**launch_args)
                except Exception as e_first:
                    try:
                        la = dict(launch_args)
                        la.pop("channel", None)
                        browser = await p.chromium.launch(**la)
                    except Exception as e_second:
                        last_proxy_error_str = str(e_second or e_first)
                        status.event(f"Ошибка запуска браузера: {last_proxy_error_str}")
                        status.push()
                        await asyncio.sleep(2)
                        continue

                try:
                    is_mobile = (viewport or {}).get("width", 1000) <= 480
                    context_kwargs = {
                        "user_agent": user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                        "viewport": viewport or {"width": 1366, "height": 768},
                        "is_mobile": is_mobile,
                        "has_touch": is_mobile,
                    }
                    if context_overrides:
                        context_kwargs.update(context_overrides)

                    context = await browser.new_context(**context_kwargs)
                    await add_stealth_scripts(context, stealth_js)
                    page = await context.new_page()

                    try:
                        ua_effective = await page.evaluate("() => navigator.userAgent")
                    except Exception:
                        ua_effective = context_kwargs["user_agent"]
                    vp = page.viewport_size or context_kwargs.get("viewport", {"width": "-", "height": "-"})
                    status.set_profile(ua_effective, vp, is_mobile)
                    status.push()

                    login_success = False
                    for _ in range(MAX_LOGIN_ATTEMPTS):
                        # Проверяем статус аккаунта перед авторизацией
                        if username and username != "Без аккаунта" and worker_id is not None:
                            acc_status = await account_manager.get_account_status(username)
                            if acc_status and acc_status.get("banned") and acc_status.get("ban_worker_id") != worker_id:
                                status.set_state(f"Аккаунт забанен другим воркером: {acc_status.get('ban_reason', 'unknown')}", "🚫")
                                status.event(f"Работа остановлена из-за бана в другом воркере")
                                status.push()
                                return {"status": "other_worker_banned", "reason": acc_status.get("ban_reason")}
                                
                        result = await login_krisha(page, username, password)
                        if result == "invalid_credentials":
                            status.set_state("Неверный логин/пароль", "🔴")
                            status.event("Авторизация отклонена")
                            status.push()
                            return "invalid_credentials"
                        elif result == "account_blocked":
                            status.set_state("Аккаунт заблокирован", "🚫")
                            status.event("Блокировка при авторизации")
                            status.push()
                            
                            # Отмечаем аккаунт как забаненный
                            if username and username != "Без аккаунта" and worker_id is not None:
                                await account_manager.mark_banned(username, worker_id, "account_blocked")
                            
                            if acc_shared:
                                acc_shared["banned"] = True
                                acc_shared["ban_reason"] = "account_blocked"
                                
                            return "account_blocked"
                        if result == "success":
                            status.set_state("Авторизация успешна", "✅")
                            status.event("Вход выполнен")
                            status.push()
                            login_success = True
                            break
                        await asyncio.sleep(2)

                    if login_success:
                        break
                    else:
                        await browser.close()
                        browser = None
                        continue

                except Exception as e:
                    last_proxy_error_str = str(e)
                    status.event(f"Старт/контекст: {last_proxy_error_str}")
                    status.push()
                    try:
                        if browser:
                            await browser.close()
                    except Exception:
                        pass
                    browser = None
                    await asyncio.sleep(2)

            if browser is None:
                status.set_state("Ошибка прокси/сети", "❌")
                status.event("Не удалось запустить браузер")
                status.push()
                return "proxy_error"
            elif not login_success:
                err = (last_proxy_error_str or "").lower()
                if any(k in err for k in PROXY_ERROR_KEYWORDS):
                    status.set_state("Ошибка прокси/сети", "❌")
                    status.push()
                    return "proxy_error"
                else:
                    status.set_state("Авторизация не удалась", "❌")
                    status.push()
                    return "auth_failed"

            try:
                await navigate_with_retries(page, "https://krisha.kz", wait_until="domcontentloaded")
                try:
                    await page.evaluate("() => document.querySelectorAll('.tutorial__descr--visible').forEach(el => el.remove())")
                except Exception:
                    pass
            except Exception:
                pass

            today = datetime.now().date()
            first_category_visit = True

            while not account_restricted and unsubscribed < max_unsubscribes:
                # Периодически проверяем не забанен ли аккаунт в другом воркере
                if username and username != "Без аккаунта" and worker_id is not None:
                    acc_status = await account_manager.get_account_status(username)
                    if acc_status and acc_status.get("banned") and acc_status.get("ban_worker_id") != worker_id:
                        status.set_state(f"Аккаунт забанен другим воркером: {acc_status.get('ban_reason', 'unknown')}", "🚫")
                        status.event(f"Работа остановлена из-за бана в другом воркере")
                        status.push()
                        return {"status": "other_worker_banned", "reason": acc_status.get("ban_reason")}
                
                # Проверяем статус через общий словарь
                if acc_shared and acc_shared.get("banned"):
                    status.set_state(f"Аккаунт забанен другим воркером: {acc_shared.get('ban_reason', 'unknown')}", "🚫")
                    status.event(f"Работа остановлена из-за бана в другом воркере")
                    status.push()
                    return {"status": "other_worker_banned"}
                
                for cat_url in categories:
                    # Проверка на баны
                    if acc_shared and acc_shared.get("banned"):
                        break
                    if account_restricted or unsubscribed >= max_unsubscribes:
                        break
                    
                    # Проверяем статус через менеджер аккаунтов
                    if username and username != "Без аккаунта" and worker_id is not None:
                        acc_status = await account_manager.get_account_status(username)
                        if acc_status and acc_status.get("banned") and acc_status.get("ban_worker_id") != worker_id:
                            status.set_state(f"Аккаунт забанен другим воркером: {acc_status.get('ban_reason', 'unknown')}", "🚫")
                            status.event(f"Работа остановлена из-за бана в другом воркере")
                            status.push()
                            return {"status": "other_worker_banned", "reason": acc_status.get("ban_reason")}

                    status.set_current_category(cat_url)
                    status.set_state("Поиск объявлений…", "🔎")
                    status.event("Открываю категорию")
                    status.push()

                    url = cat_url
                    page_count = 0

                    while True:
                        # Проверка на баны
                        if acc_shared and acc_shared.get("banned"):
                            break
                        if account_restricted or unsubscribed >= max_unsubscribes:
                            break
                            
                        # Проверяем статус через менеджер аккаунтов
                        if username and username != "Без аккаунта" and worker_id is not None:
                            acc_status = await account_manager.get_account_status(username)
                            if acc_status and acc_status.get("banned") and acc_status.get("ban_worker_id") != worker_id:
                                status.set_state(f"Аккаунт забанен другим воркером: {acc_status.get('ban_reason', 'unknown')}", "🚫")
                                status.event(f"Работа остановлена из-за бана в другом воркере")
                                status.push()
                                return {"status": "other_worker_banned", "reason": acc_status.get("ban_reason")}

                        try:
                            await navigate_with_retries(page, url, wait_until="domcontentloaded")
                        except Exception as e:
                            em = str(e)
                            status.event(f"Навигация к категории: {em}")
                            status.push()
                            if _is_proxy_or_network_error(em) or _is_chrome_error_url(getattr(page, 'url', '')):  # расширили кейворды
                                break
                            continue

                        if first_category_visit:
                            try:
                                modal = await page.wait_for_selector('.tutorial__descr--visible', state="visible", timeout=10000)
                                if modal:
                                    await page.mouse.click(100, 100)
                            except Exception:
                                pass
                            first_category_visit = False

                        page_count += 1
                        if page_count > MAX_PAGES_PER_CATEGORY:
                            status.event(f"Лимит страниц категории: {MAX_PAGES_PER_CATEGORY}")
                            status.push()
                            break

                        cards = await page.query_selector_all('section.a-list .a-card')
                        owner_ads = []
                        for card in cards:
                            # Проверка на баны
                            if acc_shared and acc_shared.get("banned"):
                                break
                            if account_restricted or unsubscribed >= max_unsubscribes:
                                break
                                
                            try:
                                is_owner = await card.query_selector('.label--yellow.label-user-owner')
                                if not is_owner:
                                    continue
                                stats_items = await card.query_selector_all('.a-card__stats-item')
                                date_str = ""
                                for stat in stats_items:
                                    stat_text = (await stat.inner_text()).strip()
                                    if re.match(r"\d{1,2}\s[а-я]{3}\.?", stat_text.lower()):
                                        date_str = stat_text
                                        break
                                if not date_str:
                                    continue
                                pub_date = parse_krisha_date(date_str)
                                if not pub_date or pub_date != today:
                                    continue
                                url_el = await card.query_selector('a.a-card__image')
                                href = await url_el.get_attribute('href') if url_el else None
                                if href:
                                    ad_url = f"https://krisha.kz{href}"
                                    if ad_url not in [ad['url'] for ad in owner_ads]:
                                        owner_ads.append({"url": ad_url})
                            except Exception:
                                continue

                        if not owner_ads:
                            paginator_next = await page.query_selector('div.paginator__btn-text:has-text("Дальше")')
                            if paginator_next and page_count < MAX_PAGES_PER_CATEGORY:
                                await _pause(BETWEEN_PAGES_DELAY_SEC)
                                parent_btn = await paginator_next.evaluate_handle('el => el.closest(".paginator__btn")')
                                if parent_btn:
                                    try:
                                        await parent_btn.click()
                                        await page.wait_for_load_state("domcontentloaded")
                                        url = page.url
                                        continue
                                    except Exception:
                                        pass
                            break

                        for ad in owner_ads:
                            # Проверка на баны
                            if acc_shared and acc_shared.get("banned"):
                                break
                            if account_restricted or unsubscribed >= max_unsubscribes:
                                break
                                
                            # Проверяем статус через менеджер аккаунтов
                            if username and username != "Без аккаунта" and worker_id is not None:
                                acc_status = await account_manager.get_account_status(username)
                                if acc_status and acc_status.get("banned") and acc_status.get("ban_worker_id") != worker_id:
                                    status.set_state(f"Аккаунт забанен другим воркером: {acc_status.get('ban_reason', 'unknown')}", "🚫")
                                    status.event(f"Работа остановлена из-за бана в другом воркере")
                                    status.push()
                                    return {"status": "other_worker_banned", "reason": acc_status.get("ban_reason")}
                                
                            if not ad['url'] or is_ad_sent(ad['url']):
                                continue

                            tab = None
                            try:
                                tab = await context.new_page()
                                try:
                                    await navigate_with_retries(tab, ad['url'], wait_until="domcontentloaded")
                                except Exception:
                                    if tab:
                                        await tab.close()
                                    continue

                                navbar_items = await tab.query_selector_all("ul.navbar-menu li")
                                menu_items_text = []
                                for item in navbar_items:
                                    try:
                                        text = await item.inner_text()
                                        menu_items_text.append(text.strip().lower())
                                    except Exception:
                                        pass
                                if any("регистрация" in t for t in menu_items_text) and any("личный кабинет" in t for t in menu_items_text):
                                    status.set_state("Аккаунт выкинут из авторизации", "🚨")
                                    status.event("Сессия потеряна")
                                    status.push()
                                    account_restricted = True
                                    
                                    # Отмечаем аккаунт как забаненный
                                    if username and username != "Без аккаунта" and worker_id is not None:
                                        await account_manager.mark_banned(username, worker_id, "session_lost")
                                    
                                    if acc_shared:
                                        acc_shared["banned"] = True
                                        acc_shared["ban_reason"] = "session_lost"
                                        
                                    break

                                seller_id = await get_seller_id(tab)
                                if seller_id and is_seller_blacklisted(seller_id):
                                    await tab.close()
                                    continue

                                await _pause(PRE_MESSAGE_DELAY_SEC)
                                await tab.evaluate("window.scrollTo(0, 200)")

                                parsed_data = {}
                                if parse_title:
                                    try:
                                        title_element = await tab.query_selector('.offer__advert-title h1')
                                        parsed_data['title'] = (await title_element.inner_text()).strip() if title_element else None
                                    except Exception:
                                        parsed_data['title'] = None
                                if parse_price:
                                    try:
                                        price_element = await tab.query_selector('body > main > div.layout__container.a-item > div > div.offer__container > div > div.offer__advert-info > div.offer__sidebar-header > div')
                                        price_text = await price_element.inner_text() if price_element else None
                                        parsed_data['price'] = extract_price(price_text) if price_text else None
                                    except Exception:
                                        parsed_data['price'] = None
                                if parse_name:
                                    try:
                                        if '/my/messages/' in tab.url:
                                            name_element = await tab.wait_for_selector('.mes-user-info__primary', state="visible", timeout=7000)
                                            name = await name_element.inner_text() if name_element else None
                                            parsed_data['name'] = name.strip() if name else None
                                        else:
                                            modal = await tab.query_selector('.tutorial__descr--visible')
                                            if modal:
                                                await tab.mouse.click(10, 400)
                                            try:
                                                msg_btn = await tab.wait_for_selector('a.message-send-button', state="visible", timeout=7000)
                                                await msg_btn.click()
                                                await tab.wait_for_load_state("domcontentloaded")
                                                name_element = await tab.wait_for_selector('.mes-user-info__primary', state="visible", timeout=7000)
                                                name = await name_element.inner_text() if name_element else None
                                                parsed_data['name'] = name.strip() if name else None
                                            except Exception:
                                                parsed_data['name'] = None
                                        if parsed_data.get('name') and "Пользователь приложения" in parsed_data['name']:
                                            status.set_state("Аккаунт ограничен", "🚨")
                                            status.push()
                                            account_restricted = True
                                            
                                            # Отмечаем аккаунт как забаненный
                                            if username and username != "Без аккаунта" and worker_id is not None:
                                                await account_manager.mark_banned(username, worker_id, "restricted")
                                                
                                            if acc_shared:
                                                acc_shared["banned"] = True
                                                acc_shared["ban_reason"] = "restricted"
                                                
                                            break
                                    except Exception:
                                        parsed_data['name'] = None
                                
                                if isinstance(custom_text, str) and custom_text.strip().startswith("["):
                                    try:
                                        custom_text = json.loads(custom_text)
                                    except Exception as e:
                                        print(f"Ошибка парсинга custom_text: {e}")

                                my_custom_text = pick_custom_text(custom_text)
                                # Проверяем наличие плейсхолдера {link} или [link]
                                has_link_placeholder = my_custom_text and (
                                    "{link}" in my_custom_text.lower() or 
                                    "[link]" in my_custom_text.lower()
                                )

                                # Генерация ссылки через API Manager
                                if has_link_placeholder and api_manager and api_manager.enabled:
                                    status.event("🔗 Генерация ссылки через API...")
                                    status.push()
                                    
                                    try:
                                        # Получаем данные для API
                                        title_for_api = parsed_data.get('title', 'Объявление')[:64]
                                        price_for_api = parsed_data.get('price')
                                        
                                        status.event(f"📌 Title: {title_for_api[:30]}...")
                                        status.event(f"💰 Price: {price_for_api}")
                                        status.push()
                                        
                                        # Вызываем API Manager (phone - это title для Bastart)
                                        shortened_link = await api_manager.get_link(
                                            phone=title_for_api
                                        )
                                        
                                        if shortened_link:
                                            parsed_data['link'] = shortened_link
                                            status.event(f"✅ Ссылка получена: {shortened_link[:40]}...")
                                        else:
                                            # Fallback на URL объявления
                                            parsed_data['link'] = ad['url']
                                            status.event(f"⚠️ API не дал ссылку, используем URL объявления")
                                    except Exception as e:
                                        # Fallback на URL объявления при ошибке
                                        parsed_data['link'] = ad['url']
                                        status.event(f"❌ Ошибка API: {type(e).__name__}")
                                        status.event(f"Используем URL объявления как fallback")
                                    
                                    status.push()
                                else:
                                    # Если нет API или плейсхолдера - используем URL объявления
                                    if has_link_placeholder:
                                        parsed_data['link'] = ad['url']
                                        status.event("🔗 API отключен, используем URL объявления")
                                        status.push()
                                final_message_text = replace_placeholders(my_custom_text, **parsed_data)
                                normalized_text = normalize_message_text(final_message_text)

                                if not normalized_text:
                                    await tab.close()
                                    continue

                                try:
                                    if '/my/messages/' not in tab.url:
                                        msg_btn = await tab.wait_for_selector('a.message-send-button', state="visible", timeout=8000)
                                        await msg_btn.click()
                                        await tab.wait_for_load_state("domcontentloaded")
                                except Exception:
                                    pass

                                try:
                                    input_selector = 'span.footer__input[contenteditable="true"]'
                                    input_locator = tab.locator(input_selector)
                                    await input_locator.wait_for(state="visible", timeout=10000)
                                except Exception:
                                    await tab.close()
                                    continue

                                await _pause(CHAT_READY_DELAY_SEC)

                                # Вставка одним сообщением
                                try:
                                    await tab.evaluate("""(text) => {
                                        const ta = document.createElement('textarea');
                                        ta.value = text;
                                        document.body.appendChild(ta);
                                        ta.select();
                                        document.execCommand('copy');
                                        document.body.removeChild(ta);
                                    }""", normalized_text)
                                    await input_locator.click()
                                    await tab.keyboard.press('Control+V')
                                except Exception:
                                    try:
                                        await tab.evaluate("""(payload) => {
                                            const { text, sel } = payload;
                                            const el = document.querySelector(sel);
                                            if (!el) return;
                                            el.focus();
                                            el.textContent = text;
                                        }""", {"text": normalized_text, "sel": input_selector})
                                    except Exception:
                                        await tab.close()
                                        continue

                                await _pause(PASTE_BEFORE_SEND_DELAY_SEC)
                                try:
                                    await tab.keyboard.press("Enter")
                                except Exception:
                                    await tab.close()
                                    continue

                                ok, _ = await confirm_message_sent(tab, input_selector, normalized_text, timeout_sec=VERIFY_SENT_TIMEOUT_SEC)
                                await _pause(POST_SEND_SETTLE_DELAY_SEC)
                                # ОТПРАВКА ССЫЛКИ ВТОРЫМ СООБЩЕНИЕМ (если был плейсхолдер)
                                if has_link_placeholder and parsed_data.get('link'):
                                    status.event("📎 Отправка ссылки вторым сообщением...")
                                    status.push()
                                    
                                    await asyncio.sleep(1.5)  # Пауза между сообщениями
                                    
                                    try:
                                        link_to_send = parsed_data['link']
                                        
                                        # Вставляем ссылку через буфер обмена
                                        await tab.evaluate("""(link) => {
                                            const ta = document.createElement('textarea');
                                            ta.value = link;
                                            document.body.appendChild(ta);
                                            ta.select();
                                            document.execCommand('copy');
                                            document.body.removeChild(ta);
                                        }""", link_to_send)
                                        
                                        await input_locator.click()
                                        await tab.keyboard.press('Control+V')
                                        await asyncio.sleep(0.5)
                                        
                                        try:
                                            await tab.keyboard.press("Enter")
                                            status.event(f"✅ Ссылка отправлена: {link_to_send[:40]}...")
                                        except Exception:
                                            status.event("⚠️ Не удалось отправить Enter")
                                        
                                        status.push()
                                        await asyncio.sleep(1.0)
                                        
                                    except Exception as e:
                                        status.event(f"⚠️ Ошибка отправки ссылки: {str(e)[:50]}")
                                        status.push()

                                await global_throttle()
                                await _pause(BETWEEN_MESSAGES_DELAY_SEC)

                                if await check_account_restriction(tab):
                                    status.set_state("Аккаунт ограничен", "🚨")
                                    status.push()
                                    account_restricted = True
                                    
                                    # Отмечаем аккаунт как забаненный
                                    if username and username != "Без аккаунта" and worker_id is not None:
                                        await account_manager.mark_banned(username, worker_id, "restricted")
                                        
                                    if acc_shared:
                                        acc_shared["banned"] = True
                                        acc_shared["ban_reason"] = "restricted"
                                        
                                    break
                                else:
                                    add_sent_ad(ad['url'])
                                    increment_message_count(1)
                                    unsubscribed += 1
                                    status.inc_sent(1)
                                    status.set_state("Отправлено сообщений", "📨")
                                    status.push()
                                    if seller_id:
                                        add_blacklisted_seller(seller_id)

                            except Exception:
                                pass
                            finally:
                                if tab:
                                    try:
                                        await tab.close()
                                    except Exception:
                                        pass

                        if unsubscribed >= max_unsubscribes or account_restricted:
                            break

                        paginator_next = await page.query_selector('div.paginator__btn-text:has-text("Дальше")')
                        if paginator_next and page_count < MAX_PAGES_PER_CATEGORY:
                            await _pause(BETWEEN_PAGES_DELAY_SEC)
                            parent_btn = await paginator_next.evaluate_handle('el => el.closest(".paginator__btn")')
                            if parent_btn:
                                try:
                                    await parent_btn.click()
                                    await page.wait_for_load_state("domcontentloaded")
                                    url = page.url
                                    continue
                                except Exception:
                                    pass
                        break  # конец одной страницы категории

                if unsubscribed >= max_unsubscribes or account_restricted:
                    break

        if acc_shared is not None:
            if account_restricted:
                acc_shared["banned"] = True
                acc_shared["ban_reason"] = "restricted"
                status.set_state("Завершено: ограничение аккаунта", "⚠️")
                status.event("Работа остановлена из-за ограничений")
            elif unsubscribed >= max_unsubscribes:
                status.set_state("Завершено: достигнут лимит", "✅")
                status.event("Достигнут лимит сообщений")
            else:
                status.set_state("Завершено", "✅")
            status.push()
            return not account_restricted
        else:
            # ВАЖНО: Для независимого режима тоже возвращаем результат
            if account_restricted:
                status.set_state("Завершено: ограничение аккаунта", "⚠️")
                status.event("Работа остановлена из-за ограничений")
                status.push()
                return False  # Явно возвращаем False при ограничении
            elif unsubscribed >= max_unsubscribes:
                status.set_state("Завершено: достигнут лимит", "✅")
                status.event("Достигнут лимит сообщений")
                status.push()
                return True  # Успешное завершение
            else:
                status.set_state("Завершено", "✅")
                status.push()
                return True  # Успешное завершение

    except Exception as e:
        low = str(e).lower()
        if any(k in low for k in PROXY_ERROR_KEYWORDS) or "chrome-error://chromewebdata/" in low or "err_aborted" in low:
            status.set_state("Критическая ошибка (прокси/сеть)", "🛑")
            status.event(str(e))
            status.push()
            return "proxy_error"
        status.set_state("Критическая ошибка", "🛑")
        status.event(str(e))
        status.push()
        # Возвращаем "error", чтобы оркестратор не трактовал как бан
        return "error"
    finally:
        # Отменяем задачу проверки статуса, если она была запущена
        if status_check_task and not status_check_task.done():
            status_check_task.cancel()
            try:
                await status_check_task
            except asyncio.CancelledError:
                pass
                
        if browser:
            try:
                await browser.close()
            except Exception:
                pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--proxy", type=str, help="Прокси (например, http://user:pass@ip:port)")
    parser.add_argument("--username", type=str, required=True, help="Логин на krisha.kz")
    parser.add_argument("--password", type=str, required=True, help="Пароль на krisha.kz")
    parser.add_argument("--headless", type=str, default="True", help="Режим без GUI (True/False)")
    parser.add_argument("--bot_token", type=str, required=True, help="Токен Telegram-бота")
    parser.add_argument("--log_chat_id", type=int, required=True, help="ID чата для логов")
    parser.add_argument("--log_message_id", type=int, required=True, help="ID сообщения для обновления логов")
    parser.add_argument("--categories", nargs='*', type=str, default=None, help="Ссылки на категории")
    parser.add_argument("--user_agent", type=str, default=None)
    parser.add_argument("--viewport", type=str, default=None, help="Формат WxH, например 1280x720")
    parser.add_argument("--worker_id", type=int, help="ID воркера для взаимодействия с менеджером аккаунтов")

    args = parser.parse_args()

    args.headless = args.headless.lower() == 'true'

    vp_dict = None
    if args.viewport:
        try:
            w, h = args.viewport.lower().replace(" ", "").split("x", 1)
            vp_dict = {"width": int(w), "height": int(h)}
        except Exception:
            vp_dict = None

    asyncio.run(
        run_krisha(
            proxy=args.proxy,
            username=args.username,
            password=args.password,
            headless=args.headless,
            bot_token=args.bot_token,
            chat_id=args.log_chat_id,
            message_id=args.log_message_id,
            categories=args.categories or [],
            user_agent=args.user_agent,
            viewport=vp_dict,
            context_overrides=None,
            worker_id=args.worker_id
        )
    )