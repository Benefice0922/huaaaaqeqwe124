import sqlite3
import json
from datetime import datetime
from urllib.parse import urlparse
import threading

_DB_PATH = "worker_data.db"
_db_lock = threading.Lock()

def get_conn():
    # check_same_thread=False позволяет использовать соединение из разных потоков
    return sqlite3.connect(_DB_PATH, check_same_thread=False)

def init_db():
    """Инициализация всех таблиц в базе данных."""
    conn = get_conn()
    cur = conn.cursor()

    # --- Прокси ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS proxies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT NOT NULL,
            port TEXT NOT NULL,
            username TEXT,
            password TEXT,
            protocol TEXT DEFAULT 'http'
        )
    """)

    # --- Аккаунты ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # --- Cookie аккаунты ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cookie_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            content TEXT
        )
    """)

    # --- Пользователи (администраторы бота) ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            username TEXT,
            first_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --- Глобальные настройки ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # --- Настройки платформ ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS platform_settings (
            platform TEXT NOT NULL,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            PRIMARY KEY (platform, key)
        )
    """)

    # --- Отправленные объявления (анти-дубли) ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sent_ads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad_url TEXT NOT NULL UNIQUE,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --- Статистика ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY,
            total_messages_sent INTEGER DEFAULT 0,
            last_mailing_start TIMESTAMP,
            last_mailing_end TIMESTAMP
        )
    """)
    cur.execute("INSERT OR IGNORE INTO stats (id, total_messages_sent) VALUES (1, 0)")

    # --- Чёрный список продавцов ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS blacklisted_sellers (
            seller_id TEXT PRIMARY KEY
        )
    """)

    # Индексы
    cur.execute("CREATE INDEX IF NOT EXISTS idx_proxies_ip_port ON proxies(ip, port)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_platform_settings ON platform_settings(platform, key)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_sent_ads_url ON sent_ads(ad_url)")

    conn.commit()
    conn.close()


def normalize_url(ad_url):
    """Убирает query и fragment, оставляет только базовый URL."""
    parts = urlparse(ad_url)
    return f"{parts.scheme}://{parts.netloc}{parts.path}"

# --------- УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ ---------
def save_user(user_id, first_name, username):
    """Сохраняет или обновляет пользователя."""
    with _db_lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO users (user_id, first_name, username, first_login)
            VALUES (?, ?, ?, COALESCE((SELECT first_login FROM users WHERE user_id = ?), CURRENT_TIMESTAMP))
        """, (user_id, first_name, username, user_id))
        conn.commit()
        conn.close()

def get_user(user_id):
    """Возвращает данные пользователя."""
    with _db_lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT user_id, first_name, username, first_login FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        conn.close()
    if row:
        return {
            "user_id": row[0],
            "first_name": row[1],
            "username": row[2],
            "first_login": row[3]
        }
    return None

# --------- PROXY FUNCTIONS ---------
def add_proxy(ip, port, username=None, password=None, protocol="http"):
    with _db_lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("INSERT INTO proxies (ip, port, username, password, protocol) VALUES (?, ?, ?, ?, ?)",
                    (ip, port, username, password, protocol))
        conn.commit()
        conn.close()

def delete_proxy(proxy_id):
    with _db_lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM proxies WHERE id=?", (proxy_id,))
        conn.commit()
        conn.close()

def delete_all_proxies():
    with _db_lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM proxies")
        conn.commit()
        conn.close()

def get_proxies():
    with _db_lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM proxies")
        proxies = cur.fetchall()
        conn.close()
    return proxies

# --------- ACCOUNT FUNCTIONS ---------
def add_account(username, password):
    with _db_lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("INSERT INTO accounts (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()

def delete_account(account_id):
    with _db_lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM accounts WHERE id=?", (account_id,))
        conn.commit()
        conn.close()

def delete_all_accounts():
    with _db_lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM accounts")
        conn.commit()
        conn.close()

def get_accounts():
    with _db_lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM accounts")
        accounts = cur.fetchall()
        conn.close()
    return accounts

def remove_account(acc):
    """
    Удаляет аккаунт по id.
    Используется в account_pool.py
    """
    with _db_lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM accounts WHERE id=?", (acc[0],))
        conn.commit()
        conn.close()

# --------- COOKIE ACCOUNT FUNCTIONS ---------
def add_cookie_account(filename, content):
    with _db_lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("INSERT INTO cookie_accounts (filename, content) VALUES (?, ?)", (filename, content))
        conn.commit()
        conn.close()

def get_cookie_accounts():
    with _db_lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, filename FROM cookie_accounts")
        result = cur.fetchall()
        conn.close()
    return result

def get_cookie_account_content(account_id):
    with _db_lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT content FROM cookie_accounts WHERE id=?", (account_id,))
        row = cur.fetchone()
        conn.close()
    return row[0] if row else None

def delete_cookie_account(account_id):
    with _db_lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM cookie_accounts WHERE id=?", (account_id,))
        conn.commit()
        conn.close()

def delete_all_cookie_accounts():
    with _db_lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM cookie_accounts")
        conn.commit()
        conn.close()

# --------- ГЛОБАЛЬНЫЕ НАСТРОЙКИ ---------
def get_settings():
    with _db_lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT key, value FROM settings")
        rows = cur.fetchall()
        conn.close()

    settings = {}
    for key, value in rows:
        settings[key] = parse_value(value)

    defaults = {
        "browser_visible": False,
        "without_proxy": False,
        "autostart_timer": None
    }
    for k, v in defaults.items():
        if k not in settings:
            settings[k] = v
    return settings

def set_setting(key, value):
    with _db_lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, serialize_value(value)))
        conn.commit()
        conn.close()

# --------- НАСТРОЙКИ ПЛОЩАДОК ---------
def get_platform_settings(platform):
    with _db_lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT key, value FROM platform_settings WHERE platform = ?", (platform,))
        rows = cur.fetchall()
        conn.close()

    settings = {}
    for k, v in rows:
        settings[k] = parse_value(v)

    if "multithread" not in settings:
        settings["multithread"] = False
    return settings

def set_platform_setting(platform, key, value):
    with _db_lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO platform_settings (platform, key, value)
            VALUES (?, ?, ?)
        """, (platform, key, serialize_value(value)))
        conn.commit()
        conn.close()

# --------- ОТПРАВЛЕННЫЕ ОБЪЯВЛЕНИЯ ---------
def add_sent_ad(ad_url):
    url_norm = normalize_url(ad_url)
    with _db_lock:
        conn = get_conn()
        cur = conn.cursor()
        try:
            cur.execute("INSERT OR IGNORE INTO sent_ads (ad_url) VALUES (?)", (url_norm,))
            conn.commit()
        finally:
            conn.close()

def is_ad_sent(ad_url):
    url_norm = normalize_url(ad_url)
    with _db_lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM sent_ads WHERE ad_url = ?", (url_norm,))
        result = cur.fetchone()
        conn.close()
    return result is not None

def get_total_sent_count():
    with _db_lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM sent_ads")
        count = cur.fetchone()[0]
        conn.close()
    return count

def remove_sent_ad(ad_url):
    url_norm = normalize_url(ad_url)
    with _db_lock:
        conn = get_conn()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM sent_ads WHERE ad_url = ?", (url_norm,))
            conn.commit()
        except Exception as e:
            print(f"[DB ERROR] Не удалось удалить запись для {ad_url}: {e}")
        finally:
            conn.close()

# --------- ЧЕРНЫЙ СПИСОК ПРОДАВЦОВ ---------
def add_blacklisted_seller(seller_id):
    """Добавляет seller_id в черный список продавцов."""
    with _db_lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO blacklisted_sellers (seller_id) VALUES (?)", (seller_id,))
        conn.commit()
        conn.close()

def is_seller_blacklisted(seller_id):
    """Проверяет, находится ли seller_id в черном списке продавцов."""
    with _db_lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM blacklisted_sellers WHERE seller_id=?", (seller_id,))
        result = cur.fetchone()
        conn.close()
    return result is not None

def get_blacklisted_seller_count():
    with _db_lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM blacklisted_sellers")
        count = cur.fetchone()[0]
        conn.close()
    return count

# --------- СТАТИСТИКА ---------
def increment_message_count(n=1):
    with _db_lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("UPDATE stats SET total_messages_sent = total_messages_sent + ? WHERE id = 1", (n,))
        conn.commit()
        conn.close()

def set_last_mailing_start():
    with _db_lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("UPDATE stats SET last_mailing_start = ? WHERE id = 1", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))
        conn.commit()
        conn.close()

def set_last_mailing_end():
    with _db_lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("UPDATE stats SET last_mailing_end = ? WHERE id = 1", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))
        conn.commit()
        conn.close()

def get_stats():
    with _db_lock:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT total_messages_sent, last_mailing_start, last_mailing_end FROM stats WHERE id = 1")
        row = cur.fetchone()
        conn.close()
    if row:
        return {
            "total_messages_sent": row[0],
            "last_mailing_start": row[1],
            "last_mailing_end": row[2]
        }
    return {"total_messages_sent": 0, "last_mailing_start": None, "last_mailing_end": None}

# --------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---------
def parse_value(value):
    if value is None or value == "None":
        return None
    if value == "True":
        return True
    if value == "False":
        return False
    if isinstance(value, str) and value.startswith("[") and value.endswith("]"):
        try:
            return json.loads(value.replace("'", '"'))
        except:
            pass
    try:
        return int(value)
    except:
        pass
    return value

def serialize_value(value):
    if isinstance(value, (list, tuple, dict)):
        return json.dumps(value, ensure_ascii=False)
    elif isinstance(value, bool):
        return str(value)
    elif value is None:
        return "None"
    else:
        return str(value)