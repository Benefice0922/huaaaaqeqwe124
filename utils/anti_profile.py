from __future__ import annotations
from typing import Optional, Dict
from datetime import datetime
import random
import json

def decide_color_scheme(timezone_id: Optional[str]) -> str:
    try:
        from dateutil import tz
        tzinfo = tz.gettz(timezone_id) if timezone_id else None
        now = datetime.now(tzinfo) if tzinfo else datetime.utcnow()
        hour = now.hour
        return "dark" if (hour >= 20 or hour < 6) else "light"
    except Exception:
        return "light"

def choose_device_scale_factor(viewport: Dict[str, int]) -> float:
    w = viewport.get("width", 1366)
    if w >= 2560:
        return random.choice([1.0, 1.25, 1.5])
    if w >= 1920:
        return random.choice([1.0, 1.25])
    return random.choice([1.0, 1.0, 1.25])

def build_context_overrides(*, viewport: Dict[str, int], geo: Optional[Dict]) -> Dict:
    overrides: Dict = {}
    if geo:
        langs = geo.get("languages") or ["en-US"]
        overrides["locale"] = langs[0]
        overrides["timezone_id"] = geo.get("timezone") or None
        if geo.get("lat") is not None and geo.get("lon") is not None:
            overrides["geolocation"] = {"latitude": float(geo["lat"]), "longitude": float(geo["lon"])}
            overrides["permissions"] = ["geolocation"]
        overrides["extra_http_headers"] = {"Accept-Language": geo.get("accept_language") or ",".join(langs)}
        overrides["color_scheme"] = decide_color_scheme(overrides.get("timezone_id"))
    else:
        overrides["locale"] = "en-US"
        overrides["color_scheme"] = "light"
    overrides["device_scale_factor"] = choose_device_scale_factor(viewport)
    return overrides

def _noise_by_level(level: str) -> float:
    lvl = (level or "medium").lower()
    if lvl == "low":
        return 0.001
    if lvl == "high":
        return 0.02
    return 0.005  # medium

def build_stealth_js(config: Dict) -> str:
    """
    config:
      platform_str, hardware_concurrency, device_memory, max_touch_points, color_depth,
      webgl_vendor, webgl_renderer, noise_level
    """
    platform_str = json.dumps(config.get("platform_str", "Win32"))
    hc = int(config.get("hardware_concurrency") or 8)
    dm = int(config.get("device_memory") or 8)
    mtp = int(config.get("max_touch_points") or 0)
    cd = int(config.get("color_depth") or 24)
    webgl_vendor = json.dumps(config.get("webgl_vendor", "Google Inc. (Intel)"))
    webgl_renderer = json.dumps(config.get("webgl_renderer", "ANGLE (Intel, Intel(R) Iris Xe Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)"))
    shift = _noise_by_level(config.get("noise_level") or "medium")

    return f"""
(() => {{
  try {{
    // Индикация инъекции
    try {{ window.__fp_stealth = "ok"; }} catch (e) {{}}

    const overrideRO = (obj, prop, val) => {{
      try {{
        Object.defineProperty(obj, prop, {{ get: () => val, configurable: true }});
      }} catch (e) {{}}
    }};

    // Navigator
    overrideRO(navigator, 'platform', {platform_str});
    overrideRO(navigator, 'hardwareConcurrency', {hc});
    if ('deviceMemory' in navigator) {{
      overrideRO(navigator, 'deviceMemory', {dm});
    }} else {{
      try {{ Object.defineProperty(navigator, 'deviceMemory', {{ get: () => {dm}, configurable: true }}); }} catch (e) {{}}
    }}
    overrideRO(navigator, 'maxTouchPoints', {mtp});

    // Screen
    if (window.screen) {{
      try {{ Object.defineProperty(window.screen, 'colorDepth', {{ get: () => {cd}, configurable: true }}); }} catch (e) {{}}
    }}

    // Canvas noise (немутирующий)
    const toDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function() {{
      try {{
        const src = this;
        const w = src.width, h = src.height;
        if (!w || !h) return toDataURL.apply(src, arguments);
        const copy = document.createElement('canvas');
        copy.width = w; copy.height = h;
        const cctx = copy.getContext('2d');
        cctx.drawImage(src, 0, 0);
        const img = cctx.getImageData(0, 0, w, h);
        const data = img.data;
        const shift = {shift};
        for (let i = 0; i < data.length; i += 4) {{
          data[i]     = Math.min(255, data[i] + shift);
          data[i + 1] = Math.min(255, data[i + 1] + shift);
          data[i + 2] = Math.min(255, data[i + 2] + shift);
        }}
        cctx.putImageData(img, 0, 0);
        return toDataURL.apply(copy, arguments);
      }} catch (e) {{
        return toDataURL.apply(this, arguments);
      }}
    }};

    // WebGL: обёртка getContext с прокси WebGL-объекта
    const VENDOR = 0x1F00;   // gl.VENDOR
    const RENDERER = 0x1F01; // gl.RENDERER
    const UV = 0x9245;       // UNMASKED_VENDOR_WEBGL
    const UR = 0x9246;       // UNMASKED_RENDERER_WEBGL

    function wrapGL(gl) {{
      if (!gl || gl.__fp_wrapped) return gl;
      const originalGetParameter = gl.getParameter?.bind(gl);
      const originalGetExtension = gl.getExtension?.bind(gl);
      const handler = {{
        get(target, prop, receiver) {{
          if (prop === 'getParameter') {{
            return function(pname) {{
              if (pname === VENDOR || pname === UV) return {webgl_vendor};
              if (pname === RENDERER || pname === UR) return {webgl_renderer};
              try {{ return originalGetParameter ? originalGetParameter(pname) : undefined; }} catch(e) {{ return null; }}
            }};
          }}
          if (prop === 'getExtension') {{
            return function(name) {{
              const ext = originalGetExtension ? originalGetExtension(name) : null;
              if (name === 'WEBGL_debug_renderer_info') {{
                return ext || Object.freeze({{ UNMASKED_VENDOR_WEBGL: UV, UNMASKED_RENDERER_WEBGL: UR }});
              }}
              return ext;
            }};
          }}
          return Reflect.get(target, prop, receiver);
        }}
      }};
      const proxy = new Proxy(gl, handler);
      try {{ Object.defineProperty(proxy, '__fp_wrapped', {{ value: true }}) }} catch(e) {{}}
      return proxy;
    }}

    // Оборачиваем HTMLCanvasElement.getContext
    if (HTMLCanvasElement && HTMLCanvasElement.prototype && HTMLCanvasElement.prototype.getContext) {{
      const origGetContext = HTMLCanvasElement.prototype.getContext;
      HTMLCanvasElement.prototype.getContext = function(type, attrs) {{
        const ctx = origGetContext.call(this, type, attrs);
        if (!type) return ctx;
        const t = String(type).toLowerCase();
        if (t === 'webgl' || t === 'experimental-webgl' || t === 'webgl2') {{
          return wrapGL(ctx);
        }}
        return ctx;
      }};
    }}

    // Оборачиваем OffscreenCanvas.getContext (если есть)
    if (typeof OffscreenCanvas !== 'undefined' && OffscreenCanvas.prototype && OffscreenCanvas.prototype.getContext) {{
      const origGetContext2 = OffscreenCanvas.prototype.getContext;
      OffscreenCanvas.prototype.getContext = function(type, attrs) {{
        const ctx = origGetContext2.call(this, type, attrs);
        if (!type) return ctx;
        const t = String(type).toLowerCase();
        if (t === 'webgl' || t === 'experimental-webgl' || t === 'webgl2') {{
          return wrapGL(ctx);
        }}
        return ctx;
      }};
    }}
  }} catch(e) {{}}
}})();
"""

async def add_stealth_scripts(page_or_context, js: Optional[str] = None) -> None:
    try:
        if js:
            await page_or_context.add_init_script(js)
        else:
            await page_or_context.add_init_script(build_stealth_js({}))
    except Exception:
        pass