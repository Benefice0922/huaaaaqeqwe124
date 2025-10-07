import asyncio
import json
from typing import Optional, Dict

import aiohttp

PROVIDERS = [
    ("https://ipapi.co/json",      "ipapi"),
    ("https://ipinfo.io/json",     "ipinfo"),
    ("http://ip-api.com/json",     "ip-api"),
]

DEFAULT_TIMEOUT = 6


def _norm_langs(country_code: str) -> list[str]:
    cc = (country_code or "").upper()
    mapping = {
        "KZ": ["ru-RU", "kk-KZ"],
        "KG": ["ru-RU", "ky-KG"],
        "RU": ["ru-RU"],
        "UA": ["uk-UA", "ru-RU"],
        "UZ": ["ru-RU", "uz-UZ"],
        "TR": ["tr-TR", "en-US"],
        "US": ["en-US"],
        "DE": ["de-DE", "en-US"],
        "FR": ["fr-FR", "en-US"],
        "ES": ["es-ES", "en-US"],
        "IT": ["it-IT", "en-US"],
        "PL": ["pl-PL", "en-US"],
        "CN": ["zh-CN", "en-US"],
    }
    return mapping.get(cc, ["en-US"])


def _accept_language(langs: list[str]) -> str:
    parts = []
    for i, l in enumerate(langs):
        if i == 0:
            parts.append(l)
        else:
            q = max(5, 10 - i) / 10  # 0.9, 0.8, ...
            parts.append(f"{l};q={q:.1f}")
    return ",".join(parts)


async def _fetch_json(session: aiohttp.ClientSession, url: str, proxy: Optional[str]) -> Optional[dict]:
    try:
        async with session.get(url, proxy=proxy, timeout=DEFAULT_TIMEOUT) as resp:
            if resp.status == 200:
                txt = await resp.text()
                return json.loads(txt)
    except Exception:
        return None
    return None


def _parse(provider: str, data: dict) -> Optional[Dict]:
    try:
        if provider == "ipapi":
            return {
                "ip": data.get("ip"),
                "country": data.get("country_name"),
                "country_code": data.get("country_code"),
                "region": data.get("region"),
                "city": data.get("city"),
                "timezone": data.get("timezone"),
                "lat": float(data.get("latitude")) if data.get("latitude") else None,
                "lon": float(data.get("longitude")) if data.get("longitude") else None,
            }
        if provider == "ipinfo":
            loc = data.get("loc") or ""
            lat, lon = None, None
            if "," in loc:
                try:
                    la, lo = loc.split(",", 1)
                    lat, lon = float(la), float(lo)
                except Exception:
                    lat, lon = None, None
            return {
                "ip": data.get("ip"),
                "country": data.get("country"),
                "country_code": data.get("country"),
                "region": "",
                "city": data.get("city"),
                "timezone": data.get("timezone"),
                "lat": lat,
                "lon": lon,
            }
        if provider == "ip-api":
            return {
                "ip": data.get("query"),
                "country": data.get("country"),
                "country_code": data.get("countryCode"),
                "region": data.get("regionName"),
                "city": data.get("city"),
                "timezone": data.get("timezone"),
                "lat": float(data.get("lat")) if data.get("lat") is not None else None,
                "lon": float(data.get("lon")) if data.get("lon") is not None else None,
            }
    except Exception:
        return None
    return None


async def resolve_geo_via_proxy(proxy: Optional[str]) -> Optional[Dict]:
    """
    Возвращает:
      {
        'country': str, 'country_code': str, 'city': str,
        'timezone': str, 'lat': float, 'lon': float,
        'languages': [primary, ...], 'accept_language': 'header'
      }
    или None.
    """
    timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT + 2)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for url, tag in PROVIDERS:
            data = await _fetch_json(session, url, proxy)
            if not data:
                continue
            parsed = _parse(tag, data)
            if not parsed:
                continue
            langs = _norm_langs(parsed.get("country_code") or "")
            return {
                **parsed,
                "languages": langs,
                "accept_language": _accept_language(langs),
            }
    return None