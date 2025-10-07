import asyncio
import argparse
import html
import json
import os
import re
import requests
import random
from urllib.parse import urlparse
from datetime import datetime, date
from typing import Optional, List, Tuple, Dict
from collections import deque

from playwright.async_api import async_playwright, Page, BrowserContext, TimeoutError as PlaywrightTimeoutError
from playwright_scripts.utils import replace_placeholders, extract_price, PLACEHOLDER_LABELS
from db import (
    is_ad_sent,
    add_sent_ad,
    add_blacklisted_seller,
    is_seller_blacklisted,
    increment_message_count
)
from utils.global_throttler import global_throttle
from utils.anti_profile import add_stealth_scripts

# ===================== CONFIG ======================
INITIAL_WAIT_AFTER_COOKIES_MS = 5000
SESSION_VALIDATE_TOTAL_TIMEOUT_MS = 20000
SESSION_VALIDATE_POLL_MS = 400
CATEGORY_AUTH_MAX_WAIT_MS = 120_000
AD_AUTH_MAX_WAIT_MS = 20_000
CATEGORY_AUTH_POLL_MS = 600
AD_AUTH_POLL_MS = 600
WAIT_AFTER_CATEGORY_NAV_SEC = 2.5
WAIT_AFTER_AD_OPEN_SEC = 2.5
SCROLL_DELAY_SEC = 1.5
SCROLL_STEP_BASE_PX = 550
SCROLL_STEP_JITTER_PX = 120
SCROLL_MAX_ITER = 120
STALL_ROUNDS_LIMIT = 6
CATEGORY_MAX_TIME_SEC = 900
ONLY_TODAY = True
SEND_BUTTON_WAIT_MS = 9000
SEND_BUTTON_POLL_MS = 250
MODAL_CLOSE_MAX_WAIT_MS = 8000
MODAL_POLL_MS = 200
SEND_RETRY_ATTEMPTS = 3

# ===================== SELECTORS ======================
PROFILE_SELECTORS = [
    "a.LFLink.14.weight-400.user-profile__name",
    "div.user-profile a.LFLink.user-profile__name",
    "div.user-profile a[href*='/account']",
    "a.user-profile__name"
]
AVATAR_SELECTORS = [
    "div.userAvatarWrapper",
    "span.userAvatar",
    ".details-page__user-info .userAvatarWrapper",
    ".user-info .userAvatarWrapper",
    ".details-page__user-info .userAvatar",
    ".userName"
]
WALLET_SELECTORS = [
    ".header-wallet-balance a",
    "a.LFLink.large.weight-400",
    "a[href*='wallet']"
]
LOGIN_MARKERS = [
    "a[href*='login']",
    "button:has-text('Войти')",
    "form[action*='login']",
    "button:has-text('Log in')",
    "a:has-text('Войти')"
]
ARTICLE_SELECTOR = "article.ad-tile-horizontal"
ARTICLE_LINK_SELECTOR = "a.ad-tile-horizontal-link"
ARTICLE_TIME_SELECTOR = "span.ad-meta-info-default__time"
ARTICLE_PRICE_SELECTOR = "p.LFSubHeading.size-14.weight-700"
ARTICLE_TITLE_SELECTOR = ".ad-tile-horizontal-header-link-title p"
CHAT_OPEN_BUTTONS = [
    "button:has-text('Написать')",
    "a:has-text('Написать')",
    "button[data-testid='write-message']",
    "a[data-testid='write-message']"
]
CHAT_INPUT_SELECTORS = [
    "textarea.msg-input",
    ".msg-input",
    "div[contenteditable='true']",
    "[data-testid='chat-input']",
    "textarea"
]
SEND_BUTTON_SELECTORS = [
    "button.LFButton.primary-green:has-text('Отправить')",
    "button:has-text('Отправить')",
    ".chat-wrapper button.primary-green:has-text('Отправить')",
]
CHAT_MODAL_WRAPPER = ".default-modal-view"
CHAT_MODAL_CLOSE_BTN = ".default-modal-view .modal__close"
MODAL_CLOSE_SELECTORS = [
    "button:has-text('Закрыть')",
    ".modal__close",
    "button.close",
    ".close-button",
    ".modal-close",
    ".LFButton:has-text('Закрыть')"
]
MODAL_OVERLAY_SELECTORS = [
    ".ReactModal__Overlay",
    ".modal",
    "[role='dialog']",
    ".popup",
    ".tutorial__descr--visible"
]
ITEM_TITLE_SELECTORS = [
    "h1.LFHeading.size-20.weight-700.ad-detail-title",
    "h1.ad-detail-title",
    "h1[data-testid='ad-title']",
    "h1"
]
SELLER_NAME_SELECTORS = [
    "span.userName-text",
    ".user-profile__name",
    ".seller-name",
    "[data-testid='seller-name']"
]
PRICE_SELECTORS = [
    "p.LFHeading.size-26.weight-700",
    ".ad-price",
    "[data-testid='ad-price']",
    ".price"
]


def pick_custom_text(custom_text):
    """
    Выбирает текст для отправки из custom_text.
    Если custom_text — список, возвращает случайный вариант.
    Если строка — возвращает её.
    Если пусто — возвращает пустую строку.
    """
    if isinstance(custom_text, list) and custom_text:
        return random.choice(custom_text)
    elif isinstance(custom_text, str):
        return custom_text
    return ""

# ===================== LOG (тонкий класс ниже) ======================
def _proxy_disp(proxy):
    if isinstance(proxy, dict):
        return proxy.get("server")
    return proxy

# ===================== COOKIE ======================
def get_cookie_data(cookie_data_arg):
    cookies_dir = os.path.join(os.getcwd(), "cookies")
    abs_path = os.path.join(cookies_dir, str(cookie_data_arg))
    if isinstance(cookie_data_arg, str) and os.path.isfile(abs_path):
        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"[COOKIE ERROR] read {abs_path}: {e}")
            return None
    if isinstance(cookie_data_arg, str) and (
        cookie_data_arg.strip().startswith("[") or
        "=" in cookie_data_arg or
        cookie_data_arg.strip().startswith("# Netscape")
    ):
        return cookie_data_arg
    if isinstance(cookie_data_arg, str):
        return cookie_data_arg
    return None

def parse_cookies(cookie_data, default_domain=".lalafo.kg"):
    if not cookie_data or not isinstance(cookie_data, str):
        raise ValueError("cookie_data пусто")
    try:
        cookies = json.loads(cookie_data)
        if isinstance(cookies, list) and cookies and isinstance(cookies[0], dict):
            return cookies
    except Exception:
        pass
    if cookie_data.strip().startswith("# Netscape HTTP Cookie File"):
        cookies = []
        for line in cookie_data.splitlines():
            if not line or line.startswith("#"):
                continue
            parts = line.strip().split("\t")
            if len(parts) == 7:
                domain, flag, path, secure, expires, name, value = parts
                cookies.append({
                    "domain": domain, "path": path,
                    "secure": secure.lower() == "true" or secure == "1",
                    "expires": int(expires) if str(expires).isdigit() else -1,
                    "name": name, "value": value, "httpOnly": False,
                })
        return cookies
    if "=" in cookie_data and ";" in cookie_data:
        cookies = []
        for pair in cookie_data.split(";"):
            if "=" in pair:
                n, v = pair.strip().split("=", 1)
                cookies.append({
                    "name": n.strip(),
                    "value": v.strip(),
                    "domain": default_domain,
                    "path": "/",
                    "expires": -1,
                    "httpOnly": False,
                    "secure": False
                })
        return cookies
    raise ValueError("Формат cookies не распознан")

# === NEW: приведение прокси к формату Playwright ===
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

def normalize_message_text(text: str) -> str:
    return (text or "").strip()

# ===================== AUTH / SESSION ======================
async def login_lalafo(page: Page, cookie_data: str) -> bool:
    try:
        cookies = parse_cookies(cookie_data)
        await page.goto("https://lalafo.kg", wait_until="domcontentloaded", timeout=45000)
        await page.context.add_cookies(cookies)
        return True
    except Exception as e:
        print(f"[LOGIN ERROR] {e}")
        return False

async def _extract_inner_text(el):
    try:
        txt = await el.inner_text()
        if txt:
            return txt.strip()
    except Exception:
        pass
    return None

def _wallet_pattern(text: str) -> bool:
    if not text:
        return False
    t = text.lower().replace("ё", "е")
    return ("кошелек" in t or "кошел" in t) and "kgs" in t

async def wait_for_chat_input(tab, timeout_ms=8000, poll_ms=200):
    import time
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        for sel in CHAT_INPUT_SELECTORS:
            try:
                el = await tab.query_selector(sel)
                if el:
                    return el
            except Exception:
                pass
        await tab.wait_for_timeout(poll_ms)
    return None

async def poll_for_profile_and_wallet(page: Page, total_timeout_ms: int, poll_ms: int):
    deadline = datetime.now().timestamp() + total_timeout_ms / 1000
    profile_name = None
    wallet_text = None
    while datetime.now().timestamp() < deadline:
        for sel in PROFILE_SELECTORS:
            try:
                el = await page.query_selector(sel)
                if el:
                    t = await _extract_inner_text(el)
                    if t and len(t) >= 2:
                        profile_name = t
                        break
            except Exception:
                continue
        for sel in WALLET_SELECTORS:
            try:
                els = await page.query_selector_all(sel)
                for el in els:
                    t = await _extract_inner_text(el)
                    if t and _wallet_pattern(t):
                        wallet_text = t
                        break
                if wallet_text:
                    break
            except Exception:
                continue
        if profile_name and wallet_text:
            return True, profile_name, wallet_text
        await page.wait_for_timeout(poll_ms)
    return False, profile_name, wallet_text

async def check_login_markers(page: Page) -> bool:
    for sel in LOGIN_MARKERS:
        try:
            el = await page.query_selector(sel)
            if el:
                return True
        except Exception:
            continue
    return False

async def wait_authorization_state(page: Page, max_wait_ms: int, poll_ms: int, log_cb, stage: str):
    start = datetime.now().timestamp()
    last_log_bucket = -1
    while (datetime.now().timestamp() - start) * 1000 < max_wait_ms:
        if await check_login_markers(page):
            return "unauthorized"
        ok, _, _ = await poll_for_profile_and_wallet(page, total_timeout_ms=poll_ms, poll_ms=poll_ms)
        if ok:
            return "authorized"
        elapsed = datetime.now().timestamp() - start
        bucket = int(elapsed // 10)
        if bucket != last_log_bucket:
            last_log_bucket = bucket
            if log_cb:
                log_cb(f"⏳ Ожидание авторизации ({stage}): {elapsed:.1f}s / {max_wait_ms/1000:.0f}s")
    return "timeout"

async def wait_account_ready(page: Page, max_wait_ms: int, poll_ms: int) -> bool:
    ok, _, _ = await poll_for_profile_and_wallet(page, total_timeout_ms=max_wait_ms, poll_ms=poll_ms)
    return ok

# ===================== MODAL HANDLING ======================
async def dismiss_modal(page: Page) -> bool:
    handled = False
    for sel in [".modal__close"] + MODAL_CLOSE_SELECTORS:
        try:
            el = await page.query_selector(sel)
            if el:
                await el.click()
                await page.wait_for_timeout(150)
                handled = True
        except Exception:
            pass
    for sel in MODAL_OVERLAY_SELECTORS:
        try:
            ov = await page.query_selector(sel)
            if ov:
                try:
                    box = await ov.bounding_box()
                    if box:
                        await page.mouse.click(box["x"] + 5, box["y"] + 5)
                        await page.wait_for_timeout(120)
                        handled = True
                except Exception:
                    pass
        except Exception:
            pass
    if not handled:
        try:
            await page.mouse.click(30, 30)
        except Exception:
            pass
    return handled

async def ensure_modal_closed(page: Page, max_wait_ms: int = MODAL_CLOSE_MAX_WAIT_MS) -> bool:
    deadline = datetime.now().timestamp() + max_wait_ms / 1000
    while datetime.now().timestamp() < deadline:
        try:
            exists = await page.query_selector(CHAT_MODAL_WRAPPER)
        except Exception:
            exists = None
        if not exists:
            return True
        await close_chat_modal_if_any(page, timeout_ms=500)
        await page.wait_for_timeout(MODAL_POLL_MS)
    try:
        return not bool(await page.query_selector(CHAT_MODAL_WRAPPER))
    except Exception:
        return True

async def close_chat_modal_if_any(page: Page, timeout_ms: int = 4000) -> bool:
    try:
        await page.wait_for_selector(CHAT_MODAL_WRAPPER, timeout=timeout_ms)
    except Exception:
        return True
    try:
        btn = await page.query_selector(CHAT_MODAL_CLOSE_BTN)
        if btn:
            await btn.click()
            await page.wait_for_timeout(200)
    except Exception:
        pass
    still = await page.query_selector(CHAT_MODAL_WRAPPER)
    if still:
        try:
            await page.mouse.click(10, 10)
            await page.wait_for_timeout(150)
        except Exception:
            pass
    still = await page.query_selector(CHAT_MODAL_WRAPPER)
    if still:
        try:
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(150)
        except Exception:
            pass
    still = await page.query_selector(CHAT_MODAL_WRAPPER)
    return not bool(still)

# ===================== DATE ======================
DATE_RE = re.compile(r"(\d{2})\.(\d{2})\.(\d{4})")

def parse_lalafo_date(date_text: str) -> date | None:
    if not date_text:
        return None
    m = DATE_RE.search(date_text)
    if not m:
        return None
    try:
        d, mth, y = map(int, m.groups())
        return date(y, mth, d)
    except Exception:
        return None

# ===================== SCROLL ======================
async def smooth_scroll_step(page: Page, base_px: int, jitter: int):
    step = base_px + random.randint(-jitter, jitter)
    chunk = 120
    scrolled = 0
    while scrolled < step:
        delta = min(chunk, step - scrolled)
        try:
            await page.evaluate("(d)=>window.scrollBy(0,d)", delta)
        except Exception:
            pass
        scrolled += delta
        await page.wait_for_timeout(40)

# ===================== GET USER_ID FROM PROFILE ======================
async def get_user_id_from_profile(tab: Page) -> str | None:
    original_url = tab.url
    try:
        user_name_element = await tab.query_selector("span.userName-text")
        if user_name_element:
            await tab.evaluate("(el) => el.scrollIntoView({behavior: 'smooth', block: 'center'})", user_name_element)
            await asyncio.sleep(1)
            await user_name_element.click()
            await asyncio.sleep(2)
            current_url = tab.url
            if ("/user/" in current_url or re.search(r"lalafo\.kg\/[^\/]+$", current_url)) and current_url != original_url:
                match = re.search(r'/user/([^/?#]+)', current_url) or re.search(r'lalafo\.kg/([^/?#]+)$', current_url)
                if match:
                    user_id = match.group(1)
                    await tab.goto(original_url, wait_until="domcontentloaded")
                    await asyncio.sleep(2)
                    return user_id
                await tab.goto(original_url, wait_until="domcontentloaded")
                await asyncio.sleep(2)
                return None
            else:
                try:
                    profile_link = await tab.query_selector("a.user-profile__name")
                    if profile_link:
                        href = await profile_link.get_attribute("href")
                        if href:
                            match = re.search(r'/user/([^/?#]+)', href) or re.search(r'/([^/?#]+)$', href)
                            if match:
                                return match.group(1)
                except Exception:
                    pass
                return None
        else:
            return None
    except Exception:
        try:
            if tab.url != original_url:
                await tab.goto(original_url, wait_until="domcontentloaded")
                await asyncio.sleep(1.5)
        except Exception:
            pass
    return None

# ===================== ПАРСИНГ ДАННЫХ ОБЪЯВЛЕНИЯ ======================
async def parse_item_details(page: Page, parse_title=False, parse_price=False, parse_name=False):
    result = {}
    if parse_title:
        for selector in ITEM_TITLE_SELECTORS:
            try:
                el = await page.query_selector(selector)
                if el:
                    title_text = await _extract_inner_text(el)
                    if title_text:
                        result["title"] = title_text
                        break
            except Exception:
                continue
    if parse_name:
        for selector in SELLER_NAME_SELECTORS:
            try:
                el = await page.query_selector(selector)
                if el:
                    name_text = await _extract_inner_text(el)
                    if name_text:
                        result["name"] = name_text
                        break
            except Exception:
                continue
    if parse_price:
        for selector in PRICE_SELECTORS:
            try:
                el = await page.query_selector(selector)
                if el:
                    price_text = await _extract_inner_text(el)
                    if price_text:
                        result["price"] = price_text.strip()
                        break
            except Exception:
                continue
    return result

# ===================== SEND (BUTTON CLICK LOGIC) ======================
async def wait_and_click_send_button(tab: Page) -> bool:
    deadline = datetime.now().timestamp() + SEND_BUTTON_WAIT_MS / 1000
    while datetime.now().timestamp() < deadline:
        await ensure_modal_closed(tab, max_wait_ms=600)
        for sel in SEND_BUTTON_SELECTORS:
            try:
                btn = await tab.query_selector(sel)
                if not btn:
                    continue
                disabled_attr = await btn.get_attribute("disabled")
                aria_disabled = await btn.get_attribute("aria-disabled")
                if disabled_attr is None and (aria_disabled is None or aria_disabled == "false"):
                    try:
                        await tab.evaluate("(el) => el.scrollIntoView({behavior: 'smooth', block: 'center'})", btn)
                        await tab.wait_for_timeout(300)
                        await btn.click()
                        return True
                    except Exception:
                        pass
            except Exception:
                continue
        await tab.wait_for_timeout(SEND_BUTTON_POLL_MS)
    return False

# ===================== MESSAGE SENDING ======================
async def send_chat_message(tab: Page, final_message_text: str) -> bool:
    try:
        await wait_account_ready(tab, max_wait_ms=AD_AUTH_MAX_WAIT_MS, poll_ms=AD_AUTH_POLL_MS)
    except Exception:
        pass

    input_el = await wait_for_chat_input(tab, timeout_ms=5000, poll_ms=200)
    if not input_el:
        for sel in CHAT_OPEN_BUTTONS:
            try:
                btn = await tab.query_selector(sel)
                if btn:
                    try:
                        await tab.evaluate("(el) => el.scrollIntoView({behavior: 'smooth', block: 'center'})", btn)
                        await tab.wait_for_timeout(300)
                        await btn.click()
                        await tab.wait_for_timeout(1000)
                        break
                    except Exception:
                        pass
            except Exception:
                pass
        input_el = await wait_for_chat_input(tab, timeout_ms=7000, poll_ms=300)
        if not input_el:
            return False

    for attempt in range(1, SEND_RETRY_ATTEMPTS + 1):
        await ensure_modal_closed(tab, max_wait_ms=1000)
        try:
            await tab.evaluate("(el)=>el.scrollIntoView({block:'center', behavior:'smooth'})", input_el)
            await tab.wait_for_timeout(500)
        except Exception:
            pass

        try:
            tag = (await input_el.evaluate("el => el.tagName")).lower()
            if tag == "textarea":
                await input_el.fill("")
                await input_el.type(final_message_text, delay=20)
            else:
                await tab.evaluate("""
                    (el, val) => {
                        if (el.isContentEditable) {
                            el.focus();
                            el.innerHTML = "";
                            el.appendChild(document.createTextNode(val));
                        } else {
                            try { el.value = val; } catch(e){}
                        }
                    }
                """, input_el, final_message_text)
        except Exception:
            await tab.wait_for_timeout(500)
            continue

        clicked = await wait_and_click_send_button(tab)
        if clicked:
            await asyncio.sleep(1.2)
            return True

        try:
            await input_el.press("Enter")
            await asyncio.sleep(1.2)
            return True
        except Exception:
            pass

        await tab.wait_for_timeout(800)

    return False

# ===================== SAFE GOTO AND WAIT PROFILE ======================
async def safe_goto_and_wait_profile(page: Page, url, profile_selectors, max_retries=3, load_timeout=20000, poll_ms=400):
    import time
    for attempt in range(1, max_retries + 1):
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=load_timeout)
        except Exception:
            pass
        t0 = time.time()
        found = False
        while time.time() - t0 < load_timeout / 1000:
            for sel in profile_selectors:
                el = None
                try:
                    el = await page.query_selector(sel)
                except Exception:
                    pass
                if el:
                    found = True
                    break
            if found:
                break
            await page.wait_for_timeout(poll_ms)
        if found:
            return True
        else:
            try:
                await page.evaluate("window.stop()")
                await page.reload()
            except Exception:
                pass
            await page.wait_for_timeout(1500)
    return False

# ============ КРАСИВЫЙ ЛОГГЕР ============
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
        lines.append("🤖 <b>Lalafo Worker</b>")
        lines.append(f"👤 Аккаунт: <code>{html.escape(self.username)}</code>")
        lines.append(f"🛰️ Прокси: <code>{html.escape(str(self.proxy_text))}</code>")
        lines.append(f"🧩 Устройство: {'📱' if self.is_mobile else '🖥️'} {self.vp}")
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
        url = f"https://api.telegram.org/bot{self.bot_token}/editMessageText"
        data = {
            "chat_id": self.chat_id,
            "message_id": self.message_id,
            "text": self.render(),
            "parse_mode": "HTML",
        }
        try:
            requests.post(url, data=data, timeout=10)
        except Exception as e:
            print(f"[LOG ERROR] Failed to edit message via API: {e}")

# ===================== MAIN ======================
async def safe_goto_and_wait_profile(page: Page, url, profile_selectors, max_retries=3, load_timeout=20000, poll_ms=400):
    import time
    for attempt in range(1, max_retries + 1):
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=load_timeout)
        except Exception:
            pass
        t0 = time.time()
        found = False
        while time.time() - t0 < load_timeout / 1000:
            for sel in profile_selectors:
                el = None
                try:
                    el = await page.query_selector(sel)
                except Exception:
                    pass
                if el:
                    found = True
                    break
            if found:
                break
            await page.wait_for_timeout(poll_ms)
        if found:
            return True
        else:
            try:
                await page.evaluate("window.stop()")
                await page.reload()
            except Exception:
                pass
            await page.wait_for_timeout(1500)
    return False

async def run_lalafo(
    proxy,
    username,
    password,
    headless,
    bot_token,
    chat_id,
    message_id,
    platform_settings=None,
    categories=None,
    cookie_data=None,
    user_agent: str | None = None,
    viewport: dict | None = None,
    context_overrides: dict | None = None,
    stealth_js: str | None = None,
):
    global ONLY_TODAY, SESSION_VALIDATE_TOTAL_TIMEOUT_MS, SESSION_VALIDATE_POLL_MS, INITIAL_WAIT_AFTER_COOKIES_MS
    global CATEGORY_AUTH_MAX_WAIT_MS, AD_AUTH_MAX_WAIT_MS, CATEGORY_AUTH_POLL_MS, AD_AUTH_POLL_MS
    global SEND_BUTTON_WAIT_MS, SEND_BUTTON_POLL_MS, MODAL_CLOSE_MAX_WAIT_MS, MODAL_POLL_MS

    if (not cookie_data) and platform_settings and platform_settings.get("cookie_data"):
        cookie_data = platform_settings["cookie_data"]
    raw_cookie_data = get_cookie_data(cookie_data)
    if not raw_cookie_data:
        status = StatusLogger(bot_token, chat_id, message_id, username, proxy, categories or [], platform_settings.get("max_unsubscribes") or 25 if platform_settings else 25)
        status.set_state("Не удалось загрузить cookie_data", "❌")
        status.push()
        return False

    if platform_settings:
        if platform_settings.get("only_today") is not None:
            ONLY_TODAY = bool(platform_settings["only_today"])
        mapping = [
            ("validation_total_timeout_ms", "SESSION_VALIDATE_TOTAL_TIMEOUT_MS"),
            ("validation_poll_ms", "SESSION_VALIDATE_POLL_MS"),
            ("validation_initial_wait_ms", "INITIAL_WAIT_AFTER_COOKIES_MS"),
            ("auth_wait_category_ms", "CATEGORY_AUTH_MAX_WAIT_MS"),
            ("auth_wait_ad_ms", "AD_AUTH_MAX_WAIT_MS"),
            ("auth_poll_ms", "CATEGORY_AUTH_POLL_MS"),
            ("send_button_wait_ms", "SEND_BUTTON_WAIT_MS"),
            ("send_button_poll_ms", "SEND_BUTTON_POLL_MS"),
            ("modal_close_max_wait_ms", "MODAL_CLOSE_MAX_WAIT_MS"),
            ("modal_poll_ms", "MODAL_POLL_MS"),
        ]
        for key, var_name in mapping:
            if platform_settings.get(key) is not None:
                try:
                    globals()[var_name] = int(platform_settings[key])
                except Exception:
                    pass
        AD_AUTH_POLL_MS = CATEGORY_AUTH_POLL_MS

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
        selectors = platform_settings.get("selectors", []) or []
        if isinstance(selectors, str):
            selectors = [selectors]
    parse_name = "Парс имени" in selectors
    parse_price = "Парс цены" in selectors
    parse_title = "Парс названия" in selectors

    messages_sent = 0
    account_restricted = False

    # Новый статус-логер
    status = StatusLogger(bot_token, chat_id, message_id, username, proxy, categories, max_unsubscribes)
    status.set_state("Загрузка cookies и запуск…", "🔐")
    status.push()

    launch_args = {"headless": headless, "channel": "chrome"}
    proxy_conf = _coerce_playwright_proxy(proxy)
    if proxy_conf:
        launch_args["proxy"] = proxy_conf

    MAX_PROXY_ATTEMPTS = 3
    browser = None
    last_proxy_error_str = ""

    try:
        async with async_playwright() as p:
            for attempt in range(1, MAX_PROXY_ATTEMPTS + 1):
                try:
                    browser = await p.chromium.launch(**launch_args)
                    break
                except Exception as e:
                    last_proxy_error_str = str(e)
                    status.event(f"Ошибка запуска браузера: {last_proxy_error_str}")
                    status.push()
                    await asyncio.sleep(2)

            if browser is None:
                status.set_state("Не удалось подключиться к прокси", "❌")
                status.push()
                return "proxy_error"

            is_mobile = (viewport or {}).get("width", 1000) <= 480
            context_kwargs = {
                "user_agent": user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                "viewport": viewport or {"width": 1366, "height": 768},
                "is_mobile": is_mobile,
                "has_touch": is_mobile,
            }
            if context_overrides:
                context_kwargs.update(context_overrides)

            context: BrowserContext = await browser.new_context(**context_kwargs)
            await add_stealth_scripts(context, stealth_js)
            page = await context.new_page()

            try:
                ua_effective = await page.evaluate("() => navigator.userAgent")
            except Exception:
                ua_effective = context_kwargs["user_agent"]
            vp = page.viewport_size or context_kwargs.get("viewport", {"width": "-", "height": "-"})
            status.set_profile(ua_effective, vp, is_mobile)
            status.push()

            if not await login_lalafo(page, raw_cookie_data):
                status.set_state("Ошибка при установке cookies", "❌")
                status.push()
                return False

            status.set_state(f"Ждём {INITIAL_WAIT_AFTER_COOKIES_MS/1000:.1f}с перед reload…", "⏳")
            status.push()
            await page.wait_for_timeout(INITIAL_WAIT_AFTER_COOKIES_MS)

            try:
                await page.reload()
            except Exception:
                pass

            status.set_state("Валидация профиля/кошелька…", "🔎")
            status.push()
            ok, prof, wallet = await poll_for_profile_and_wallet(
                page,
                total_timeout_ms=SESSION_VALIDATE_TOTAL_TIMEOUT_MS,
                poll_ms=SESSION_VALIDATE_POLL_MS
            )

            if not ok:
                status.set_state("Сессия не валидна (нет профиля/кошелька)", "🚫")
                status.push()
                return False

            status.event(f"Профиль: {prof} | Кошелек: {wallet}")
            status.set_state("Старт обработки категорий", "🚀")
            status.push()

            today = datetime.now().date()

            for cat_url in categories:
                if account_restricted or messages_sent >= max_unsubscribes:
                    break

                status.set_current_category(cat_url)
                status.set_state("Открываю категорию…", "🧭")
                status.push()
                category_start_ts = datetime.now().timestamp()

                category_ok = await safe_goto_and_wait_profile(page, cat_url, PROFILE_SELECTORS, max_retries=3, load_timeout=20000, poll_ms=400)
                if not category_ok:
                    status.set_state("Ошибка: категория не загрузилась (профиль не найден)", "❌")
                    status.event("Аккаунт уходит из пула")
                    status.push()
                    account_restricted = True
                    break

                await page.wait_for_timeout(int(WAIT_AFTER_CATEGORY_NAV_SEC * 1000))
                await dismiss_modal(page)

                def cat_log(msg):
                    if msg.startswith("⏳ Ожидание авторизации"):
                        status.event(msg)
                        # Обновляем не чаще раза в ~10 сек
                        status.push()

                auth_state = await wait_authorization_state(
                    page,
                    max_wait_ms=CATEGORY_AUTH_MAX_WAIT_MS,
                    poll_ms=CATEGORY_AUTH_POLL_MS,
                    log_cb=cat_log,
                    stage="категория"
                )

                if auth_state != "authorized":
                    status.set_state(f"Авторизация в категории не подтверждена ({auth_state})", "🚨")
                    status.push()
                    account_restricted = True
                    break

                seen_ads = set()

                for scroll_iter in range(1, SCROLL_MAX_ITER + 1):
                    if messages_sent >= max_unsubscribes or account_restricted:
                        break
                    if datetime.now().timestamp() - category_start_ts > CATEGORY_MAX_TIME_SEC:
                        status.event("Таймаут категории")
                        status.push()
                        break

                    try:
                        articles = await page.query_selector_all(ARTICLE_SELECTOR)
                    except Exception:
                        articles = []

                    new_cards = []
                    for art in articles:
                        try:
                            a = await art.query_selector(ARTICLE_LINK_SELECTOR)
                            if not a:
                                continue
                            href = await a.get_attribute("href")
                            if not href:
                                continue
                            if not href.startswith("http"):
                                href = f"https://lalafo.kg{href}"

                            is_today = False
                            try:
                                time_el = await art.query_selector(ARTICLE_TIME_SELECTOR)
                                ttxt = await _extract_inner_text(time_el) if time_el else None
                                if ttxt:
                                    raw_date = ttxt.split("/")[0].strip()
                                    ad_d = parse_lalafo_date(raw_date)
                                    if ad_d == today:
                                        is_today = True
                            except Exception:
                                pass
                            if not is_today:
                                continue

                            if href in seen_ads or is_ad_sent(href):
                                continue

                            new_cards.append((href, art))
                        except Exception:
                            continue

                    if not new_cards:
                        break

                    for href, art in new_cards:
                        if messages_sent >= max_unsubscribes or account_restricted:
                            break
                        seen_ads.add(href)
                        tab = None
                        try:
                            tab = await context.new_page()
                            ad_ok = await safe_goto_and_wait_profile(tab, href, PROFILE_SELECTORS, max_retries=3, load_timeout=20000, poll_ms=400)
                            if not ad_ok:
                                add_sent_ad(href)
                                account_restricted = True
                                break

                            try:
                                await tab.goto(href, wait_until="domcontentloaded")
                                await tab.wait_for_load_state("load")
                            except Exception as e:
                                err = str(e).lower()
                                if any(k in err for k in ["proxy", "timeout", "network", "connection", "net::"]):
                                    status.set_state("Прокси/сеть упала при открытии объявления", "❌")
                                    status.push()
                                    return "proxy_error"
                                else:
                                    add_sent_ad(href)
                                    continue
                            await tab.wait_for_timeout(int(WAIT_AFTER_AD_OPEN_SEC * 1000))

                            user_id = await get_user_id_from_profile(tab)
                            if not user_id:
                                add_sent_ad(href)
                                await tab.close()
                                continue
                            if is_seller_blacklisted(user_id):
                                add_sent_ad(href)
                                await tab.close()
                                continue

                            parsed_data = await parse_item_details(
                                tab,
                                parse_title=parse_title,
                                parse_price=parse_price,
                                parse_name=parse_name
                            )
                            if isinstance(custom_text, str) and custom_text.strip().startswith("["):
                                try:
                                    custom_text = json.loads(custom_text)
                                except Exception as e:
                                    print(f"Ошибка парсинга custom_text: {e}")

                            my_custom_text = pick_custom_text(custom_text)
                            final_message_text = replace_placeholders(my_custom_text, **parsed_data)
                            normalized_text = normalize_message_text(final_message_text)

                            if not normalized_text:
                                add_sent_ad(href)
                                await tab.close()
                                continue

                            sent_ok = False
                            try:
                                for send_attempt in range(3):
                                    sent_ok = await send_chat_message(tab, normalized_text)
                                    if sent_ok:
                                        break
                                    else:
                                        await asyncio.sleep(2.5)
                            except Exception:
                                sent_ok = False

                            if sent_ok:
                                await global_throttle()
                                await asyncio.sleep(random.uniform(5, 10))
                                add_sent_ad(href)
                                increment_message_count(1)
                                messages_sent += 1
                                status.inc_sent(1)
                                status.set_state("Отправлено сообщений", "📨")
                                status.push()
                                add_blacklisted_seller(user_id)
                            else:
                                add_sent_ad(href)
                        finally:
                            if tab:
                                try:
                                    await tab.close()
                                except Exception:
                                    pass

                if messages_sent >= max_unsubscribes or account_restricted:
                    break

            # Завершение
            if account_restricted:
                status.set_state("Завершено: ограничение/потеря авторизации", "⚠️")
                status.event("Работа остановлена")
            elif messages_sent >= max_unsubscribes:
                status.set_state("Завершено: достигнут лимит", "✅")
                status.event("Достигнут лимит сообщений")
            else:
                status.set_state("Завершено", "✅")
            status.push()
            return not account_restricted

    except Exception as e:
        err_str = str(e)
        low = err_str.lower()
        if any(k in low for k in ["proxy", "network", "connection", "timeout", "econnrefused",
                                   "could not reach", "err_proxy_connection_failed",
                                   "err_connection_timed_out", "net::err_proxy_connection_failed",
                                   "page.goto: timeout", "browser closed"]):
            status.set_state("Критическая ошибка (прокси/сеть)", "🛑")
            status.event(err_str)
            status.push()
            return "proxy_error"
        status.set_state("Критическая ошибка", "🛑")
        status.event(err_str)
        status.push()
        return False
    finally:
        if browser:
            try:
                await browser.close()
            except Exception:
                pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--proxy", type=str, help="Прокси (например, http://user:pass@ip:port)")
    parser.add_argument("--username", type=str, required=True, help="Имя cookie-файла (логическое имя аккаунта)")
    parser.add_argument("--password", type=str, required=False, help="Не используется (заглушка)")
    parser.add_argument("--headless", type=str, default="True", help="True/False")
    parser.add_argument("--bot_token", type=str, required=True, help="Токен Telegram-бота")
    parser.add_argument("--log_chat_id", type=int, required=True)
    parser.add_argument("--log_message_id", type=int, required=True)
    parser.add_argument("--categories", nargs='*', type=str, default=None)
    parser.add_argument("--cookie_data", type=str, required=True, help="Имя файла в ./cookies или строка cookies")
    parser.add_argument("--user_agent", type=str, default=None)
    parser.add_argument("--viewport", type=str, default=None, help="Формат WxH, например 1280x720")

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
        run_lalafo(
            proxy=args.proxy,
            username=args.username,
            password=args.password or "",
            headless=args.headless,
            bot_token=args.bot_token,
            chat_id=args.log_chat_id,
            message_id=args.log_message_id,
            categories=args.categories or [],
            cookie_data=args.cookie_data,
            user_agent=args.user_agent,
            viewport=vp_dict,
            context_overrides=None,
        )
    )