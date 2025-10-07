import re
from aiogram import Router, F, Bot, types
from aiogram.fsm.context import FSMContext
from keyboards.proxy_accounts import (
    get_proxy_menu,
    get_accounts_type_menu,
    get_accounts_menu,
    get_cookie_accounts_menu,
    get_back_menu,
    get_delete_proxy_menu,
    get_delete_account_menu,
    get_delete_cookie_account_menu,
)
from db import (
    add_proxy, delete_proxy, delete_all_proxies, get_proxies,
    add_account, delete_account, delete_all_accounts, get_accounts,
    add_cookie_account, get_cookie_accounts, get_cookie_account_content,
    delete_cookie_account, delete_all_cookie_accounts,
)
from handlers.accounts_fsm import AccountsStates, CookieStates
from handlers.proxy_fsm import ProxyStates

router = Router()
router.event_types = {"message", "callback_query"} 

# ---- Вспомогательный парсер прокси (поддержка множества форматов) ----
HOST_RE = re.compile(r"^(?P<host>(?:\d{1,3}\.){3}\d{1,3}|[A-Za-z0-9\-._~%]+)$")

def _normalize_scheme(s: str | None) -> str:
    if not s:
        return "http"
    s = s.lower().strip()
    if s in ("http", "https"):
        return "http"
    if s in ("socks", "socks5", "socks5h"):
        return "socks5"
    if s in ("socks4", "socks4a"):
        return "socks4"
    return "http"

def parse_proxy_line(line: str):
    s = (line or "").strip()
    if not s or s.startswith("#") or s.startswith("//"):
        return None
    # scheme://[user:pass@]host:port
    if "://" in s:
        scheme, rest = s.split("://", 1)
        scheme = _normalize_scheme(scheme)
        user = pwd = None
        if "@" in rest:
            creds, hostport = rest.split("@", 1)
            if ":" in creds:
                user, pwd = creds.split(":", 1)
            else:
                user, pwd = creds, ""
        else:
            hostport = rest
        if ":" not in hostport:
            return None
        host, port = hostport.rsplit(":", 1)
        host, port = host.strip(), port.strip()
        if not port.isdigit() or not HOST_RE.match(host):
            return None
        return {"ip": host, "port": port, "username": user or None, "password": pwd or None, "protocol": scheme}
    # user:pass@host:port
    if "@" in s and ":" in s.split("@", 1)[1]:
        creds, hostport = s.split("@", 1)
        host, port = hostport.rsplit(":", 1)
        user, pwd = (creds.split(":", 1) + [""])[:2]
        host, port = host.strip(), port.strip()
        if not port.isdigit() or not HOST_RE.match(host):
            return None
        return {"ip": host, "port": port, "username": user or None, "password": pwd or None, "protocol": "http"}
    # поддержка префикса "socks5 " или "http "
    if s.lower().startswith("socks5 ") or s.lower().startswith("socks4 ") or s.lower().startswith("http "):
        parts = s.split(None, 1)
        scheme = _normalize_scheme(parts[0])
        rest = parts[1] if len(parts) > 1 else ""
        s = rest.strip()
        # дальше разбор как без схемы
        # провалимся ниже
    # ip:port or ip:port:user:pass or ip:port:user:pass:scheme
    parts = s.split(":")
    if len(parts) == 2:
        host, port = parts
        host, port = host.strip(), port.strip()
        if not port.isdigit() or not HOST_RE.match(host):
            return None
        return {"ip": host, "port": port, "username": None, "password": None, "protocol": "http"}
    if len(parts) >= 4:
        host = parts[0].strip()
        port = parts[1].strip()
        if not port.isdigit() or not HOST_RE.match(host):
            return None
        user = parts[2]
        # 5-й элемент может быть схемой
        if len(parts) == 5:
            pwd = parts[3]
            scheme = _normalize_scheme(parts[4])
        else:
            pwd = ":".join(parts[3:])
            scheme = "http"
        return {"ip": host, "port": port, "username": user or None, "password": pwd or None, "protocol": scheme}
    return None

# ---- ПРОКСИ ----

@router.callback_query(F.data == "proxy")
async def proxy_menu(callback: types.CallbackQuery, state: FSMContext = None):
    if state:
        await state.clear()
    proxies = get_proxies()
    count = len(proxies)
    proxy_lines = "\n".join([f"{p[1]}:{p[2]}" for p in proxies[:10]])
    msg = f"🛡️ <b>Прокси:</b>\n{proxy_lines if proxy_lines else '<i>Нет загруженных прокси.</i>'}\n\n"
    msg += f"<b>Количество:</b> <code>{count}</code>\n\n"
    msg += "Поддерживаемые форматы:\n" \
           "- ip:port\n- ip:port:user:pass\n- user:pass@ip:port\n" \
           "- http(s)://user:pass@ip:port\n- socks4://... / socks5://..."
    await callback.answer()
    await callback.message.edit_text(msg, reply_markup=get_proxy_menu(), parse_mode="HTML")

@router.callback_query(F.data == "proxy_load")
async def proxy_load_prompt(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text(
        "Отправьте список прокси текстом (многострочно) или .txt файлом.\n\n"
        "Примеры:\n"
        "  192.168.1.10:3128\n"
        "  192.168.1.11:1080:user:pass\n"
        "  user:pass@1.2.3.4:8080\n"
        "  https://user:pass@host:443\n"
        "  socks5://user:pass@1.2.3.4:9050\n",
        reply_markup=get_back_menu()
    )
    await state.set_state(ProxyStates.waiting_for_proxies)

@router.message(ProxyStates.waiting_for_proxies, F.text)
async def receive_proxies(message: types.Message, state: FSMContext):
    lines = (message.text or "").splitlines()
    added, skipped = 0, []
    for i, raw in enumerate(lines, start=1):
        item = parse_proxy_line(raw)
        if not item:
            if raw.strip():
                skipped.append(f"{i}: {raw.strip()}")
            continue
        try:
            add_proxy(item["ip"], item["port"], item.get("username"), item.get("password"), item.get("protocol") or "http")
            added += 1
        except Exception:
            skipped.append(f"{i}: {raw.strip()}")
    await state.clear()
    txt = f"Готово. Добавлено: <b>{added}</b>."
    if skipped:
        txt += "\n\n⚠️ Пропущены строки:\n" + "\n".join(f"- {s}" for s in skipped[:20])
        if len(skipped) > 20:
            txt += f"\n... и ещё {len(skipped) - 20}"
    await message.answer(txt, parse_mode="HTML", reply_markup=get_proxy_menu())

@router.message(ProxyStates.waiting_for_proxies, F.document)
async def receive_proxies_file(message: types.Message, state: FSMContext, bot: Bot):
    doc = message.document
    if not doc.file_name.lower().endswith(".txt"):
        await message.answer("Пожалуйста, отправьте .txt файл.", reply_markup=get_back_menu())
        return
    file = await bot.get_file(doc.file_id)
    content = await bot.download_file(file.file_path)
    text = content.read().decode("utf-8", errors="ignore")
    lines = text.splitlines()
    added, skipped = 0, []
    for i, raw in enumerate(lines, start=1):
        item = parse_proxy_line(raw)
        if not item:
            if raw.strip():
                skipped.append(f"{i}: {raw.strip()}")
            continue
        try:
            add_proxy(item["ip"], item["port"], item.get("username"), item.get("password"), item.get("protocol") or "http")
            added += 1
        except Exception:
            skipped.append(f"{i}: {raw.strip()}")
    await state.clear()
    txt = f"Готово. Добавлено из файла: <b>{added}</b>."
    if skipped:
        txt += "\n\n⚠️ Пропущены строки:\n" + "\n".join(f"- {s}" for s in skipped[:20])
        if len(skipped) > 20:
            txt += f"\n... и ещё {len(skipped) - 20}"
    await message.answer(txt, parse_mode="HTML", reply_markup=get_proxy_menu())

@router.callback_query(F.data == "proxy_delete_all")
async def proxy_delete_all(callback: types.CallbackQuery, state: FSMContext = None):
    if state:
        await state.clear()
    delete_all_proxies()
    await callback.answer("Все прокси удалены!")
    await callback.message.edit_text("Меню управления прокси:", reply_markup=get_proxy_menu())

@router.callback_query(F.data == "proxy_delete")
async def proxy_delete(callback: types.CallbackQuery, state: FSMContext = None):
    if state:
        await state.clear()
    proxies = get_proxies()
    if not proxies:
        await callback.answer("Нет прокси для удаления.")
        await callback.message.edit_text("Нет загруженных прокси.", reply_markup=get_proxy_menu())
        return
    await callback.answer()
    await callback.message.edit_text("Выберите прокси для удаления:", reply_markup=get_delete_proxy_menu(proxies))

@router.callback_query(F.data.startswith("proxy_del_"))
async def proxy_delete_one(callback: types.CallbackQuery, state: FSMContext = None):
    if state:
        await state.clear()
    proxy_id = int(callback.data.replace("proxy_del_", ""))
    delete_proxy(proxy_id)
    proxies = get_proxies()
    count = len(proxies)
    proxy_lines = "\n".join([f"{p[1]}:{p[2]}" for p in proxies[:10]])
    msg = f"🛡️ <b>Прокси:</b>\n{proxy_lines if proxy_lines else '<i>Нет загруженных прокси.</i>'}\n\n"
    msg += f"<b>Количество:</b> <code>{count}</code>"
    await callback.answer("Прокси удалён.")
    await callback.message.edit_text(msg, reply_markup=get_proxy_menu(), parse_mode="HTML")

# ---- АККАУНТЫ ----

@router.callback_query(F.data == "accounts")
async def accounts_types_menu(callback: types.CallbackQuery, state: FSMContext = None):
    """
    При входе в раздел "Аккаунты" показываем сводку: сколько аккаунтов по лог/пас и по cookies,
    а ниже — кнопки выбора типа.
    """
    if state:
        await state.clear()
    lp_count = len(get_accounts())
    ck_count = len(get_cookie_accounts())
    msg = (
        "👤 Аккаунты\n\n"
        f"• Логин/Пароль: <b>{lp_count}</b>\n"
        f"• Cookies: <b>{ck_count}</b>\n\n"
        "Выберите тип аккаунтов:"
    )
    await callback.answer()
    await callback.message.edit_text(msg, reply_markup=get_accounts_type_menu(), parse_mode="HTML")

@router.callback_query(F.data == "accounts_loginpass")
async def accounts_loginpass_menu(callback: types.CallbackQuery, state: FSMContext = None):
    if state:
        await state.clear()
    accounts = get_accounts()
    count = len(accounts)
    account_lines = "\n".join([f"{a[1]}" for a in accounts[:10]])
    msg = f"👤 <b>Аккаунты (логин/пароль):</b>\n{account_lines if account_lines else '<i>Нет загруженных аккаунтов.</i>'}\n\n"
    msg += f"<b>Количество:</b> <code>{count}</code>"
    await callback.answer()
    await callback.message.edit_text(msg, reply_markup=get_accounts_menu(), parse_mode="HTML")

def parse_account_line(s: str):
    if not s:
        return None
    s = s.strip()
    if not s or s.startswith("#") or s.startswith("//"):
        return None
    sep = ":" if ":" in s else ";" if ";" in s else " " if " " in s else None
    if not sep:
        return None
    login, pwd = s.split(sep, 1)
    login, pwd = login.strip(), pwd.strip()
    if not login or not pwd:
        return None
    return login, pwd

@router.callback_query(F.data == "accounts_add")
async def accounts_add(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text(
        "Отправьте список аккаунтов (txt/текст, многострочно):\n\n"
        "user1:pass1\nuser2;pass2\nuser3 pass3\n",
        reply_markup=get_back_menu()
    )
    await state.set_state(AccountsStates.waiting_for_accounts)

@router.message(AccountsStates.waiting_for_accounts, F.text)
async def receive_accounts(message: types.Message, state: FSMContext):
    lines = (message.text or "").splitlines()
    added, skipped = 0, []
    for i, raw in enumerate(lines, start=1):
        res = parse_account_line(raw)
        if not res:
            if raw.strip():
                skipped.append(f"{i}: {raw.strip()}")
            continue
        login, pwd = res
        try:
            add_account(login, pwd); added += 1
        except Exception:
            skipped.append(f"{i}: {raw.strip()}")
    await state.clear()
    txt = f"Добавлено аккаунтов: <b>{added}</b>."
    if skipped:
        txt += "\n\n⚠️ Пропущены строки:\n" + "\n".join(f"- {s}" for s in skipped[:20])
        if len(skipped) > 20:
            txt += f"\n... и ещё {len(skipped) - 20}"
    await message.answer(txt, parse_mode="HTML", reply_markup=get_accounts_menu())

@router.message(AccountsStates.waiting_for_accounts, F.document)
async def receive_accounts_file(message: types.Message, state: FSMContext, bot: Bot):
    doc = message.document
    if not doc.file_name.lower().endswith(".txt"):
        await message.answer("Пожалуйста, отправьте .txt файл.", reply_markup=get_back_menu())
        return
    file = await bot.get_file(doc.file_id)
    content = await bot.download_file(file.file_path)
    text = content.read().decode("utf-8", errors="ignore")
    lines = text.splitlines()
    added, skipped = 0, []
    for i, raw in enumerate(lines, start=1):
        res = parse_account_line(raw)
        if not res:
            if raw.strip():
                skipped.append(f"{i}: {raw.strip()}")
            continue
        login, pwd = res
        try:
            add_account(login, pwd); added += 1
        except Exception:
            skipped.append(f"{i}: {raw.strip()}")
    await state.clear()
    txt = f"Добавлено аккаунтов из файла: <b>{added}</b>."
    if skipped:
        txt += "\n\n⚠️ Пропущены строки:\n" + "\n".join(f"- {s}" for s in skipped[:20])
        if len(skipped) > 20:
            txt += f"\n... и ещё {len(skipped) - 20}"
    await message.answer(txt, parse_mode="HTML", reply_markup=get_accounts_menu())

@router.callback_query(F.data == "accounts_delete_all")
async def accounts_delete_all(callback: types.CallbackQuery, state: FSMContext = None):
    if state:
        await state.clear()
    delete_all_accounts()
    await callback.answer("Все аккаунты удалены!")
    await callback.message.edit_text("Меню управления аккаунтами:", reply_markup=get_accounts_menu())

@router.callback_query(F.data == "accounts_delete")
async def accounts_delete(callback: types.CallbackQuery, state: FSMContext = None):
    if state:
        await state.clear()
    accounts = get_accounts()
    if not accounts:
        await callback.answer("Нет аккаунтов для удаления.")
        await callback.message.edit_text("Нет загруженных аккаунтов.", reply_markup=get_accounts_menu())
        return
    await callback.answer()
    await callback.message.edit_text("Выберите аккаунт для удаления:", reply_markup=get_delete_account_menu(accounts))

@router.callback_query(F.data.startswith("acc_del_"))
async def account_delete_one(callback: types.CallbackQuery, state: FSMContext = None):
    if state:
        await state.clear()
    acc_id = int(callback.data.replace("acc_del_", ""))
    delete_account(acc_id)
    accounts = get_accounts()
    count = len(accounts)
    account_lines = "\n".join([f"{a[1]}" for a in accounts[:10]])
    msg = f"👤 <b>Аккаунты:</b>\n{account_lines if account_lines else '<i>Нет загруженных аккаунтов.</i>'}\n\n"
    msg += f"<b>Количество:</b> <code>{count}</code>"
    await callback.answer("Аккаунт удалён.")
    await callback.message.edit_text(msg, reply_markup=get_accounts_menu(), parse_mode="HTML")

# ---- COOKIE (без изменений логики) ----

@router.callback_query(F.data == "accounts_cookie")
async def accounts_cookie_menu(callback: types.CallbackQuery, state: FSMContext = None):
    if state:
        await state.clear()
    cookie_accounts = get_cookie_accounts()
    count = len(cookie_accounts)
    lines = "\n".join([f"{a[1]}" for a in cookie_accounts[:10]])
    msg = f"🍪 <b>Cookie аккаунты:</b>\n{lines if lines else '<i>Нет cookie-аккаунтов.</i>'}\n\n"
    msg += f"<b>Количество:</b> <code>{count}</code>"
    await callback.answer()
    await callback.message.edit_text(msg, reply_markup=get_cookie_accounts_menu(), parse_mode="HTML")

@router.callback_query(F.data == "accounts_add_cookie")
async def add_cookie_file_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text("Пожалуйста, отправьте файл с cookies (.json или .txt).", reply_markup=get_back_menu())
    await state.set_state(CookieStates.waiting_for_cookie_file)

@router.message(CookieStates.waiting_for_cookie_file, F.document)
async def receive_cookie_file(message: types.Message, state: FSMContext, bot: Bot):
    doc = message.document
    is_valid = doc.file_name.lower().endswith((".json", ".txt"))
    if not is_valid:
        await message.answer("Пожалуйста, отправьте файл cookie в формате .json или .txt.", reply_markup=get_back_menu())
        return
    file = await bot.get_file(doc.file_id)
    content = await bot.download_file(file.file_path)
    text = content.read().decode("utf-8", errors="ignore")

    import os
    cookies_dir = os.path.join(os.getcwd(), "cookies")
    os.makedirs(cookies_dir, exist_ok=True)
    path_on_disk = os.path.join(cookies_dir, doc.file_name)
    with open(path_on_disk, "w", encoding="utf-8") as f:
        f.write(text)

    add_cookie_account(doc.file_name, text)
    await message.answer(f"Cookie-аккаунт добавлен: {doc.file_name}", reply_markup=get_cookie_accounts_menu())
    await state.clear()

@router.callback_query(F.data == "accounts_delete_cookie")
async def delete_cookie_account_menu(callback: types.CallbackQuery, state: FSMContext = None):
    if state:
        await state.clear()
    cookie_accounts = get_cookie_accounts()
    if not cookie_accounts:
        await callback.answer("Нет cookie-аккаунтов для удаления.")
        await callback.message.edit_text("Нет cookie-аккаунтов.", reply_markup=get_cookie_accounts_menu())
        return
    await callback.answer()
    await callback.message.edit_text("Выберите cookie-аккаунт для удаления:", reply_markup=get_delete_cookie_account_menu(cookie_accounts))

@router.callback_query(F.data.startswith("cookie_del_"))
async def delete_one_cookie_account(callback: types.CallbackQuery, state: FSMContext = None):
    if state:
        await state.clear()
    account_id = int(callback.data.replace("cookie_del_", ""))
    delete_cookie_account(account_id)
    cookie_accounts = get_cookie_accounts()
    count = len(cookie_accounts)
    lines = "\n".join([f"{a[1]}" for a in cookie_accounts[:10]])
    msg = f"🍪 <b>Cookie аккаунты:</b>\n{lines if lines else '<i>Нет cookie-аккаунтов.</i>'}\n\n"
    msg += f"<b>Количество:</b> <code>{count}</code>"
    await callback.answer("Cookie-аккаунт удалён.")
    await callback.message.edit_text(msg, reply_markup=get_cookie_accounts_menu())

@router.callback_query(F.data == "accounts_delete_all_cookie")
async def delete_all_cookie_accounts_menu(callback: types.CallbackQuery, state: FSMContext = None):
    if state:
        await state.clear()
    delete_all_cookie_accounts()
    await callback.answer("Все cookie-аккаунты удалены!")
    await callback.message.edit_text("Меню cookie-аккаунтов:", reply_markup=get_cookie_accounts_menu())

@router.callback_query(F.data == "accounts_types")
async def back_to_accounts_types(callback: types.CallbackQuery, state: FSMContext = None):
    if state:
        await state.clear()
    await accounts_types_menu(callback)

@router.callback_query(F.data == "back")
async def back_button(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await proxy_menu(callback)