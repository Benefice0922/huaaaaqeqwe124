import asyncio
import argparse
import html
from urllib.parse import urlparse
from playwright.async_api import async_playwright
from datetime import datetime, timedelta
import re
import requests
import time
import random
import json
from collections import deque
from typing import List, Union

from playwright_scripts.utils import replace_placeholders, extract_price

from db import is_ad_sent, add_sent_ad, add_blacklisted_seller, is_seller_blacklisted, increment_message_count

from utils.global_throttler import global_throttle
from utils.anti_profile import add_stealth_scripts
from utils.account_status_manager import account_manager

MONTHS_RU = {
    'янв': 1, 'фев': 2, 'мар': 3, 'апр': 4, 'май': 5, 'июн': 6,
    'июл': 7, 'авг': 8, 'сен': 9, 'окт': 10, 'ноя': 11, 'дек': 12
}

# --- БАЗОВЫЕ ЛИМИТЫ/ТАЙМИНГИ (могут быть переопределены через platform_settings) ---
MAX_PAGES_PER_CATEGORY = 15
PRE_MESSAGE_DELAY_SEC = (4.5, 6.0)            # перед началом действий в объявлении
CHAT_READY_DELAY_SEC = (4.5, 6.0)
PASTE_BEFORE_SEND_DELAY_SEC = (1.8, 4.8)
POST_SEND_SETTLE_DELAY_SEC = (1.2, 2.4)
BETWEEN_MESSAGES_DELAY_SEC = (4.0, 7.0)
BETWEEN_PAGES_DELAY_SEC = (1.5, 3.5)

# --- НАДЁЖНОСТЬ НАВИГАЦИИ/СЕТЕВЫЕ ОШИБКИ ---
GOTO_RETRY_ATTEMPTS = 3
GOTO_TIMEOUT_MS = 20000
VERIFY_SENT_TIMEOUT_SEC = 7.0
VERIFY_SENT_FIRST_PHASE_SEC = 3.0

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

def _is_proxy_or_network_error(msg: str) -> bool:
    low = (msg or "").lower()
    return any(k in low for k in PROXY_ERROR_KEYWORDS)

def _is_chrome_error_url(url: str) -> bool:
    return isinstance(url, str) and url.startswith("chrome-error://")

def pick_custom_text(custom_text):
    if isinstance(custom_text, list) and custom_text:
        return random.choice(custom_text)
    elif isinstance(custom_text, str):
        return custom_text
    return ""

# -------------------------------------------------------------------
# ЛОГГИРОВАНИЕ
# -------------------------------------------------------------------
def edit_log(bot_token, chat_id, message_id, text: Union[str, List[str]]):
    if isinstance(text, list):
        text = "\n".join(text)
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

def _proxy_disp(proxy):
    if isinstance(proxy, dict):
        return proxy.get("server")
    return proxy

def parse_kolesa_date(date_str):
    date_str = date_str.strip().lower()
    now = datetime.now()
    if "сегодня" in date_str:
        return now.date()
    if "вчера" in date_str:
        return (now - timedelta(days=1)).date()
    match = re.search(r"(\d{1,2})\s+([а-я]+)", date_str)
    if match:
        day = int(match.group(1))
        mon_str = match.group(2)[:3]
        mon = MONTHS_RU.get(mon_str)
        if mon:
            year = now.year
            try:
                parsed_date = datetime(year, mon, day).date()
                if parsed_date > now.date():
                    parsed_date = datetime(year - 1, mon, day).date()
                return parsed_date
            except ValueError:
                pass
    return None

async def get_seller_id(tab):
    try:
        seller_id = await tab.evaluate("window.digitalData?.product?.seller?.userId")
        if seller_id:
            return str(seller_id)
    except Exception:
        pass
    return None

async def check_account_restriction(tab):
    try:
        user_info_elements = await tab.query_selector_all('div.mes-user-info__primary')
        for element in user_info_elements:
            text_content = await element.text_content()
            if text_content and "Пользователь приложения" in text_content:
                return True
        return False
    except Exception:
        return False

async def login_kolesa(page, username, password):
    await page.goto("https://kolesa.kz", wait_until="domcontentloaded", timeout=45000)

    login_register_button = page.locator("a.kl-ui-button--flat", has_text="Вход и регистрация")
    await login_register_button.wait_for(state="visible")
    await login_register_button.click()

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
        alerts = await page.query_selector_all("div.alert.alert-danger")
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
                if "учетная запись заблокирована" in error_text.lower():
                    return "account_blocked"
                if "Неверно указан логин или пароль" in error_text or "Неверный логин или пароль" in error_text:
                    return "invalid_credentials"
    except Exception:
        pass

    try:
        await page.wait_for_selector(
            "body > div.cabinet > div > div.cabinet__primary-header > div > div > div > div.primary-header__wrap",
            state="visible",
            timeout=12000
        )
        return "success"
    except Exception:
        return "auth_failed"

# === Приведение прокси к формату Playwright ===
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

# === Утилиты времени/интервалов ===
def _coerce_range(v):
    # Поддержка форматов: число, [min,max], (min,max), "min..max"
    if v is None:
        return None
    if isinstance(v, (list, tuple)) and len(v) == 2:
        return (float(v[0]), float(v[1]))
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str) and ".." in v:
        a, b = v.split("..", 1)
        try:
            return (float(a.strip()), float(b.strip()))
        except Exception:
            try:
                return float(v.strip())
            except Exception:
                return None
    try:
        return float(v)
    except Exception:
        return None

def _sec(val) -> float:
    if isinstance(val, (tuple, list)) and len(val) == 2:
        return float(random.uniform(float(val[0]), float(val[1])))
    return float(val)

# === Утилиты логгера и подтверждения отправки ===
def _elapsed_str(dt_start: datetime) -> str:
    delta = datetime.now() - dt_start
    total = int(delta.total_seconds())
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def _progress_bar_emoji(current: int, total: int, width: int = 14) -> str:
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
                 username: str, proxy, categories: List[str], max_unsubscribes: int,
                 bar_width: int = 14, events_max: int = 5):
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
        self.bar_width = int(bar_width) if bar_width and int(bar_width) > 0 else 14
        self.events = deque(maxlen=int(events_max) if events_max and int(events_max) > 0 else 5)
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
        bar = _progress_bar_emoji(self.sent, self.max_unsubscribes, width=self.bar_width)
        progress_line = f"✉️ {self.sent}/{self.max_unsubscribes}  {bar}"
        elapsed = _elapsed_str(self.start_time)

        lines = []
        lines.append("🤖 <b>Kolesa Worker</b>")
        lines.append(f"👤 Аккаунт: <code>{html.escape(self.username)}</code>")
        lines.append(f"🛰️ Прокси: <code>{html.escape(str(self.proxy_text))}</code>")
        lines.append(f"🧩 Устройство: {device_icon} {self.vp}")
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
            for ev in list(self.events):
                lines.append(f"• {html.escape(ev)}")
        return "\n".join(lines)

    def push(self):
        edit_log(self.bot_token, self.chat_id, self.message_id, self.render())

def normalize_message_text(text: str) -> str:
    return (text or "").strip()

async def confirm_message_sent(page, input_selector: str, expected_text: str, timeout_sec: float = VERIFY_SENT_TIMEOUT_SEC) -> tuple[bool, str]:
    end_time = time.monotonic() + timeout_sec
    first_phase_end = time.monotonic() + VERIFY_SENT_FIRST_PHASE_SEC
    expected_norm = (expected_text or "").lower()

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

# --- Применение настроек из platform_settings ---
def _apply_runtime_settings_from_platform(platform_settings, status_logger_args: dict):
    global MAX_PAGES_PER_CATEGORY, PRE_MESSAGE_DELAY_SEC, CHAT_READY_DELAY_SEC
    global PASTE_BEFORE_SEND_DELAY_SEC, POST_SEND_SETTLE_DELAY_SEC, BETWEEN_MESSAGES_DELAY_SEC

    if not platform_settings:
        return

    if platform_settings.get("max_pages_per_category") is not None:
        try:
            MAX_PAGES_PER_CATEGORY = int(platform_settings["max_pages_per_category"])
        except Exception:
            pass

    for key, var in [
        ("pre_message_delay_sec", "PRE_MESSAGE_DELAY_SEC"),
        ("chat_ready_delay_sec", "CHAT_READY_DELAY_SEC"),
        ("paste_before_send_delay_sec", "PASTE_BEFORE_SEND_DELAY_SEC"),
        ("post_send_settle_delay_sec", "POST_SEND_SETTLE_DELAY_SEC"),
        ("between_messages_delay_sec", "BETWEEN_MESSAGES_DELAY_SEC"),
    ]:
        val = platform_settings.get(key)
        if val is not None:
            coerced = _coerce_range(val)
            if coerced is not None:
                globals()[var] = coerced

    if platform_settings.get("progress_bar_width") is not None:
        try:
            status_logger_args["bar_width"] = int(platform_settings["progress_bar_width"])
        except Exception:
            pass
    if platform_settings.get("events_max") is not None:
        try:
            status_logger_args["events_max"] = int(platform_settings["events_max"])
        except Exception:
            pass

# --- Навигация с ретраями ---
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
            # Не пытаемся жить, если всё закрыто
            if "Target page, context or browser has been closed" in str(e):
                raise
            # Бэк-офф
            await asyncio.sleep(1.2 * i)
            # Попробуем стабилизировать
            try:
                await page.goto("about:blank", wait_until="domcontentloaded", timeout=timeout_ms)
            except Exception:
                pass
    raise last_err

# ============ Основной сценарий ============
async def run_kolesa(
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
    worker_id: int = None,
):
    # Уникальный ID для этого воркера, если не передан
    if worker_id is None:
        worker_id = int(time.time() * 1000) & 0xFFFFFF
    
    # Регистрируем воркер в менеджере аккаунтов
    current_task = None
    if username and username != "Без аккаунта":
        current_task = asyncio.current_task()
        acc_status = await account_manager.register_worker(worker_id, username, current_task)
        
        # Если аккаунт уже заблокирован, завершаем работу
        if acc_status.get("banned"):
            return {"status": "other_worker_banned", "reason": acc_status.get("ban_reason")}
    
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
    today = datetime.now().date()

    # Настройки логгера (возможность переопределения ширины бара и длины ленты)
    status_logger_args = {}
    _apply_runtime_settings_from_platform(platform_settings, status_logger_args)

    # Новый статус-логгер
    status = StatusLogger(
        bot_token, chat_id, message_id, username, proxy, categories, max_unsubscribes,
        **status_logger_args
    )
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

    try:
        async with async_playwright() as p:
            for proxy_attempt in range(1, MAX_PROXY_ATTEMPTS + 1):
                try:
                    # первая попытка — с channel, затем fallback без channel
                    try:
                        browser = await p.chromium.launch(**launch_args)
                    except Exception:
                        la = dict(launch_args)
                        la.pop("channel", None)
                        browser = await p.chromium.launch(**la)

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

                    # Профиль
                    try:
                        ua_effective = await page.evaluate("() => navigator.userAgent")
                    except Exception:
                        ua_effective = context_kwargs["user_agent"]
                    vp = page.viewport_size or context_kwargs.get("viewport", {"width": "-", "height": "-"})
                    status.set_profile(ua_effective, vp, is_mobile)
                    status.push()

                    # Авторизация
                    login_success = False
                    for login_attempt in range(1, MAX_LOGIN_ATTEMPTS + 1):
                        result = await login_kolesa(page, username, password)
                        if result == "invalid_credentials":
                            status.set_state("Неверный логин/пароль", "🔴")
                            status.event("Авторизация отклонена")
                            status.push()
                            # Флаг бана для аккаунта (невалид)
                            if username and username != "Без аккаунта":
                                await account_manager.set_account_banned(username, "invalid_credentials")
                            return "invalid_credentials"
                        if result == "account_blocked":
                            status.set_state("Аккаунт заблокирован", "🚫")
                            status.push()
                            if username and username != "Без аккаунта":
                                await account_manager.set_account_banned(username, "account_blocked")
                            return "account_blocked"
                        if result == "success":
                            status.set_state("Авторизация успешна", "✅")
                            status.event("Вход выполнен")
                            status.push()
                            login_success = True
                            break
                        status.event(f"Повтор авторизации {login_attempt}/{MAX_LOGIN_ATTEMPTS}")
                        status.push()
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

            # Домашняя (Kolesa)
            try:
                await navigate_with_retries(page, "https://kolesa.kz", wait_until="domcontentloaded")
                await page.evaluate("() => document.querySelectorAll('.tutorial__descr--visible, .modal, .popup').forEach(el => el.remove())")
            except Exception:
                pass

            # Обход категорий
            for cat_url in categories:
                # Проверяем, не установлен ли флаг бана
                if username and username != "Без аккаунта":
                    if await account_manager.is_account_banned(username):
                        status.set_state("Аккаунт ограничен (другим воркером)", "🚨")
                        status.push()
                        account_restricted = True
                        break
                
                if (acc_shared and acc_shared.get("banned")) or account_restricted or unsubscribed >= max_unsubscribes:
                    break
                current_page_url = cat_url
                page_number = 1
                if account_restricted or unsubscribed >= max_unsubscribes:
                    break

                status.set_current_category(cat_url)
                status.set_state("Поиск объявлений…", "🔎")
                status.event("Открываю категорию")
                status.push()

                while True:
                    # Периодическая проверка статуса аккаунта
                    if username and username != "Без аккаунта":
                        if await account_manager.is_account_banned(username):
                            status.set_state("Аккаунт ограничен (другим воркером)", "🚨")
                            status.push()
                            account_restricted = True
                            break
                    
                    if account_restricted or unsubscribed >= max_unsubscribes:
                        break
                    if page_number > MAX_PAGES_PER_CATEGORY:
                        status.event(f"Достигнут лимит страниц категории: {MAX_PAGES_PER_CATEGORY}")
                        status.push()
                        break

                    try:
                        if not current_page_url or not current_page_url.strip():
                            status.event("Пустой или недопустимый URL категории")
                            status.push()
                            break

                        await navigate_with_retries(page, current_page_url, wait_until="domcontentloaded")
                        if _is_chrome_error_url(getattr(page, "url", "")):
                            raise RuntimeError(f"chrome-error page: {page.url}")
                    except Exception as e:
                        em = str(e)
                        status.event(f"Ошибка при переходе на страницу: {em}")
                        status.push()
                        if _is_proxy_or_network_error(em) or _is_chrome_error_url(getattr(page, "url", "")):
                            # Признаём проблему сети/прокси для этой категории и выходим
                            break
                        # Иначе пробуем следующую попытку/страницу
                        break

                    # Сбор объявлений владельцев за сегодня
                    owner_ads = []
                    try:
                        cards = await page.query_selector_all('div.a-card.js__a-card')
                        for card in cards:
                            try:
                                dealer_labels = await card.query_selector_all('span.a-label__text')
                                is_dealer_or_kolesa = False
                                for label in dealer_labels:
                                    label_text = await label.inner_text()
                                    if "От дилера" in label_text or "Авто от Kolesa.kz" in label_text:
                                        is_dealer_or_kolesa = True
                                        break
                                if is_dealer_or_kolesa:
                                    continue

                                date_element = await card.query_selector('span.a-card__param--date')
                                date_text = await date_element.inner_text() if date_element else ""
                                pub_date = parse_kolesa_date(date_text)
                                if not pub_date or pub_date != today:
                                    continue

                                url_el = await card.query_selector('a.a-card__link')
                                href = await url_el.get_attribute('href') if url_el else None
                                if href:
                                    ad_url = f"https://kolesa.kz{href}" if href.startswith('/') else href
                                    if ad_url not in [ad['url'] for ad in owner_ads]:
                                        owner_ads.append({"url": ad_url})
                            except Exception as e:
                                status.event(f"Ошибка при парсинге карточки: {str(e)}")
                                continue
                    except Exception as e:
                        status.event(f"Ошибка при парсинге карточек: {str(e)}")
                        status.push()

                    # Если объявлений нет — пробуем перейти на следующую страницу, иначе выходим из категории
                    if not owner_ads:
                        try:
                            next_page_link = await page.query_selector('a.right-arrow.next_page')
                            if next_page_link:
                                next_page_href = await next_page_link.get_attribute('href')
                                if next_page_href:
                                    current_page_url = f"https://kolesa.kz{next_page_href}" if next_page_href.startswith('/') else next_page_href
                                    page_number += 1
                                    # небольшая пауза между страницами
                                    await asyncio.sleep(_sec(BETWEEN_PAGES_DELAY_SEC))
                                    continue
                        except Exception:
                            pass
                        break  # Нет объявлений и нет следующей страницы

                    # Обработка найденных объявлений
                    for ad in owner_ads:
                        # Проверка статуса аккаунта перед каждым объявлением
                        if username and username != "Без аккаунта":
                            if await account_manager.is_account_banned(username):
                                status.set_state("Аккаунт ограничен (другим воркером)", "🚨")
                                status.push()
                                account_restricted = True
                                break
                                
                        if account_restricted or unsubscribed >= max_unsubscribes:
                            break
                        if not ad['url'] or is_ad_sent(ad['url']):
                            continue

                        tab = None
                        try:
                            tab = await context.new_page()
                            try:
                                await navigate_with_retries(tab, ad['url'], wait_until="domcontentloaded")
                            except Exception as e:
                                if tab:
                                    try:
                                        await tab.close()
                                    except Exception:
                                        pass
                                # Навигация не удалась — определим, что это сеть/прокси
                                if _is_proxy_or_network_error(str(e)):
                                    continue
                                else:
                                    continue

                            seller_id = await get_seller_id(tab)
                            if seller_id and is_seller_blacklisted(seller_id):
                                await tab.close()
                                continue

                            # Пауза перед началом действий (интервальный формат поддерживается)
                            await asyncio.sleep(_sec(PRE_MESSAGE_DELAY_SEC))
                            await tab.evaluate("window.scrollTo(0, 200)")

                            parsed_data = {}
                            if parse_title:
                                try:
                                    title_element = await tab.query_selector('h1.offer__title')
                                    title = await title_element.inner_text() if title_element else None
                                    parsed_data['title'] = title.strip() if title else None
                                except Exception:
                                    parsed_data['title'] = None
                            if parse_price:
                                try:
                                    price_element = await tab.query_selector('div.offer__price')
                                    price_text = await price_element.inner_text() if price_element else None
                                    if price_text:
                                        parsed_data['price'] = extract_price(price_text)
                                    else:
                                        parsed_data['price'] = None
                                except Exception:
                                    parsed_data['price'] = None

                            # Открытие чата
                            if parse_name or custom_text:
                                try:
                                    # Закрыть возможные модалки простым кликом
                                    modals = await tab.query_selector_all('.tutorial__descr--visible, .modal, .popup')
                                    for _ in modals:
                                        try:
                                            await tab.mouse.click(10, 10)
                                        except Exception:
                                            pass
                                except Exception:
                                    pass

                                try:
                                    msg_btn = await tab.wait_for_selector(
                                        'button.seller-phones__button.kl-ui-button--blue', state="visible", timeout=7000
                                    )
                                    await msg_btn.click()
                                except Exception as e:
                                    status.event(f"Не удалось открыть чат: {str(e)}")
                                    status.push()
                                    continue

                                if parse_name:
                                    try:
                                        name_element = await tab.wait_for_selector(
                                            'div.mes-user-info__primary', state="visible", timeout=7000
                                        )
                                        name = await name_element.inner_text() if name_element else None
                                        parsed_data['name'] = name.strip() if name else None
                                        if name and "Пользователь приложения" in name:
                                            status.set_state("Аккаунт ограничен", "🚨")
                                            status.push()
                                            account_restricted = True
                                            # Уведомляем менеджер аккаунтов о блокировке
                                            if username and username != "Без аккаунта":
                                                await account_manager.set_account_banned(username, "restricted")
                                            break
                                    except Exception:
                                        parsed_data['name'] = None
   
                            if isinstance(custom_text, str) and custom_text.strip().startswith("["):
                                try:
                                    custom_text = json.loads(custom_text)
                                except Exception as e:
                                    print(f"Ошибка парсинга custom_text: {e}")

                            my_custom_text = pick_custom_text(custom_text)
                            final_message_text = replace_placeholders(my_custom_text, **parsed_data)
                            normalized_text = normalize_message_text(final_message_text)

                            if not normalized_text:
                                await tab.close()
                                continue

                            # Ожидаем поле ввода чата
                            input_selector = 'span.footer__input[contenteditable="true"]'
                            try:
                                input_locator = tab.locator(input_selector)
                                await input_locator.wait_for(state="visible", timeout=10000)
                            except Exception:
                                await tab.close()
                                continue

                            # Даем чату стабилизироваться
                            await asyncio.sleep(_sec(CHAT_READY_DELAY_SEC))

                            # ВСТАВКА ТЕКСТА (буфер обмена -> Ctrl+V), фоллбек через evaluate
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

                            # Пауза перед отправкой и отправляем Enter
                            await asyncio.sleep(_sec(PASTE_BEFORE_SEND_DELAY_SEC))
                            try:
                                await tab.keyboard.press("Enter")
                            except Exception:
                                await tab.close()
                                continue

                            # Подтверждение отправки и пауза после
                            ok, _ = await confirm_message_sent(tab, input_selector, normalized_text, timeout_sec=VERIFY_SENT_TIMEOUT_SEC)
                            await asyncio.sleep(_sec(POST_SEND_SETTLE_DELAY_SEC))

                            # Глобальный троттлинг + пауза между сообщениями
                            await global_throttle()
                            await asyncio.sleep(_sec(BETWEEN_MESSAGES_DELAY_SEC))

                            # Проверка ограничения
                            if await check_account_restriction(tab):
                                status.set_state("Аккаунт ограничен", "🚨")
                                status.push()
                                account_restricted = True
                                if username and username != "Без аккаунта":
                                    await account_manager.set_account_banned(username, "restricted")
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
                            # Тихий пропуск, чтобы не зашумлять статус
                            pass
                        finally:
                            if tab:
                                try:
                                    await tab.close()
                                except Exception:
                                    pass

                    if unsubscribed >= max_unsubscribes or account_restricted:
                        break

                    # Пагинация (только Kolesa селекторы)
                    try:
                        next_page_link = await page.query_selector('a.right-arrow.next_page')
                        if next_page_link:
                            next_page_href = await next_page_link.get_attribute('href')
                            if next_page_href:
                                current_page_url = f"https://kolesa.kz{next_page_href}" if next_page_href.startswith('/') else next_page_href
                                page_number += 1
                                await asyncio.sleep(_sec(BETWEEN_PAGES_DELAY_SEC))
                                continue
                    except Exception:
                        pass
                    break  # конец страницы

        # Завершение
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
        err = str(e)
        status.set_state("Критическая ошибка", "🛑")
        status.event(err)
        status.push()
        low = err.lower()
        if _is_proxy_or_network_error(low):
            return "proxy_error"
        # Отдаём "error", чтобы оркестратор не трактовал как бан
        return "error"
    finally:
        # Отключаем воркер от менеджера аккаунтов
        if username and username != "Без аккаунта" and worker_id is not None and current_task:
            try:
                await account_manager.unregister_worker(worker_id, username, current_task)
            except Exception as e:
                print(f"[ACCOUNT MANAGER] Ошибка при отключении воркера: {e}")
            
        try:
            if browser:
                await browser.close()
        except Exception:
            pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--proxy", type=str, help="Прокси (например, http://user:pass@ip:port)")
    parser.add_argument("--username", type=str, required=True, help="Логин на kolesa.kz")
    parser.add_argument("--password", type=str, required=True, help="Пароль на kolesa.kz")
    parser.add_argument("--headless", type=str, default="True", help="Режим без GUI (True/False)")
    parser.add_argument("--bot_token", type=str, required=True, help="Токен Telegram-бота")
    parser.add_argument("--log_chat_id", type=int, required=True, help="ID чата для логов")
    parser.add_argument("--log_message_id", type=int, required=True, help="ID сообщения для обновления логов")
    parser.add_argument("--categories", nargs='*', type=str, default=None, help="Ссылки на категории")
    parser.add_argument("--user_agent", type=str, default=None)
    parser.add_argument("--viewport", type=str, default=None, help="Формат WxH, например 1280x720")
    parser.add_argument("--worker_id", type=int, help="Уникальный ID воркера")
    args = parser.parse_args()

    args.headless = args.headless.lower() == 'true'
    vp_dict = None
    if args.viewport:
        try:
            w, h = args.viewport.lower().replace(" ", "").split("x", 1)
            vp_dict = {"width": int(w), "height": int(h)}
        except Exception:
            vp_dict = None

    asyncio.run(run_kolesa(
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
        worker_id=args.worker_id,
    ))