import os
import random
from typing import Optional, Tuple, Dict, List

from utils import ua_store

DATA_DIR = os.path.join(os.getcwd(), "data")
UA_FILE_PATH = os.path.join(DATA_DIR, "user_agents.txt")

# Только ПК разрешения, минимум 1440x900
DESKTOP_RESOLUTIONS = [
    (2560, 1440),
    (1920, 1200),
    (1920, 1080),
    (1680, 1050),
    (1600, 900),
    (1440, 900),
]

ua_store.init()

def _read_user_agents_file() -> List[str]:
    try:
        with open(UA_FILE_PATH, "r", encoding="utf-8") as f:
            return [l.strip() for l in f.read().splitlines() if l.strip()]
    except FileNotFoundError:
        return []

def _gen_random_chrome_version() -> str:
    major = random.randint(120, 129)
    build = random.randint(0, 9999)
    patch = random.randint(0, 199)
    return f"{major}.0.{build}.{patch}"

def _random_windows_ua() -> str:
    chrome = _gen_random_chrome_version()
    return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome} Safari/537.36"

def _random_macos_ua() -> str:
    chrome = _gen_random_chrome_version()
    mac_ver = random.choice(["10_15_7", "11_2_3", "12_6_3", "13_5_2"])
    return f"Mozilla/5.0 (Macintosh; Intel Mac OS X {mac_ver}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome} Safari/537.36"

def generate_random_user_agent() -> str:
    # Всегда десктоп (Windows/Mac)
    if random.random() < 0.7:
        return _random_windows_ua()
    return _random_macos_ua()

def parse_resolution(res_str: str) -> Optional[Tuple[int, int]]:
    try:
        w, h = res_str.lower().replace(" ", "").split("x", 1)
        return int(w), int(h)
    except Exception:
        return None

class FingerprintAllocator:
    """
    Стойкий отпечаток по аккаунту:
      - UA + viewport сохраняются в БД (account_fingerprints) и возвращаются при каждом запуске
      - Новый аккаунт: берём UA из файла (без дублей) или генерируем, viewport — ПК (>=1440x900)
      - Глобальные настройки разрешения (random/fixed) влияют на первичное назначение viewport
    """
    def __init__(self, settings: dict):
        self.settings = settings or {}
        self._file_uas = []
        self._file_uas_idx = 0
        if self.settings.get("ua_source", "random") == "file":
            self._file_uas = _read_user_agents_file()
            random.shuffle(self._file_uas)

        # Уже занятые UA чтобы не дублировать при назначении новых
        self._used_uas = ua_store.get_all_user_agents()

    def _pick_new_user_agent(self) -> str:
        # 1) Из файла — без повторов
        if self.settings.get("ua_source", "random") == "file" and self._file_uas:
            while self._file_uas_idx < len(self._file_uas):
                candidate = self._file_uas[self._file_uas_idx]
                self._file_uas_idx += 1
                if candidate and candidate not in self._used_uas:
                    self._used_uas.add(candidate)
                    return candidate
        # 2) Генерируем десктопный UA — также избегаем повторов
        for _ in range(100):
            candidate = generate_random_user_agent()
            if candidate not in self._used_uas:
                self._used_uas.add(candidate)
                return candidate
        return generate_random_user_agent()

    def _choose_viewport(self) -> Dict[str, int]:
        random_resolution = self.settings.get("random_resolution", True)
        if not random_resolution:
            res = self.settings.get("screen_resolution")
            parsed = parse_resolution(res) if isinstance(res, str) else None
            if parsed:
                w, h = parsed
                return {"width": w, "height": h}
        # random из ПК-пресетов (>=1440x900)
        w, h = random.choice(DESKTOP_RESOLUTIONS)
        return {"width": w, "height": h}

    def for_account(self, account_key: Optional[str], persist: bool = True) -> Tuple[str, Dict[str, int]]:
        """
        Возвращает (user_agent, viewport)
        - Если persist=True и задан account_key — возвращает UA/viewport из БД или назначает новый и сохраняет.
        - Если persist=False или account_key=None — выдаёт эпемерный (без сохранения).
        """
        if persist and account_key:
            fp = ua_store.get_fingerprint(account_key)
            if fp:
                ua, vp, _, _ = fp
                if not vp:
                    vp = self._choose_viewport()
                    ua_store.set_fingerprint(account_key, ua, vp, is_mobile=False, has_touch=False)
                return ua, vp

            ua = self._pick_new_user_agent()
            vp = self._choose_viewport()
            ua_store.set_fingerprint(account_key, ua, vp, is_mobile=False, has_touch=False)
            return ua, vp

        # Эфемерно
        ua = self._pick_new_user_agent()
        vp = self._choose_viewport()
        return ua, vp