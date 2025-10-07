import random
from typing import Dict, Tuple, List, Optional

# Широкий пул современных и распространённых GPU
GPU_MODELS: Dict[str, List[str]] = {
    "Intel": [
        # iGPU — актуальные
        "Intel(R) Iris Xe Graphics",
        "Intel(R) Iris Xe Graphics G7",
        "Intel(R) Iris Xe Graphics G4",
        "Intel(R) UHD Graphics 770",
        "Intel(R) UHD Graphics 750",
        "Intel(R) UHD Graphics 730",
        "Intel(R) UHD Graphics 630",
        "Intel(R) UHD Graphics 620",
        "Intel(R) UHD Graphics 610",
        "Intel(R) Iris Plus Graphics 655",
        "Intel(R) HD Graphics 530",
        # Arc — дискретные
        "Intel(R) Arc A370M",
        "Intel(R) Arc A550M",
        "Intel(R) Arc A580",
        "Intel(R) Arc A750",
        "Intel(R) Arc A770",
    ],
    "NVIDIA": [
        # 40xx
        "NVIDIA GeForce RTX 4090 Laptop GPU",
        "NVIDIA GeForce RTX 4080 Laptop GPU",
        "NVIDIA GeForce RTX 4070 Laptop GPU",
        "NVIDIA GeForce RTX 4060 Laptop GPU",
        "NVIDIA GeForce RTX 4050 Laptop GPU",
        "NVIDIA GeForce RTX 4090",
        "NVIDIA GeForce RTX 4080",
        "NVIDIA GeForce RTX 4070 Ti",
        "NVIDIA GeForce RTX 4070",
        "NVIDIA GeForce RTX 4060",
        "NVIDIA GeForce RTX 4050",
        # 30xx
        "NVIDIA GeForce RTX 3090",
        "NVIDIA GeForce RTX 3080",
        "NVIDIA GeForce RTX 3080 Laptop GPU",
        "NVIDIA GeForce RTX 3070",
        "NVIDIA GeForce RTX 3070 Laptop GPU",
        "NVIDIA GeForce RTX 3060",
        "NVIDIA GeForce RTX 3060 Laptop GPU",
        "NVIDIA GeForce RTX 3050",
        "NVIDIA GeForce RTX 3050 Ti Laptop GPU",
        # 20xx
        "NVIDIA GeForce RTX 2080",
        "NVIDIA GeForce RTX 2080 SUPER",
        "NVIDIA GeForce RTX 2070",
        "NVIDIA GeForce RTX 2060",
        # GTX (распространённые и ещё живые)
        "NVIDIA GeForce GTX 1660",
        "NVIDIA GeForce GTX 1660 Ti",
        "NVIDIA GeForce GTX 1660 SUPER",
        "NVIDIA GeForce GTX 1650",
        "NVIDIA GeForce GTX 1650 Ti",
        "NVIDIA GeForce GTX 1060",
        "NVIDIA GeForce GTX 1050 Ti",
    ],
    "AMD": [
        # 7000-серия
        "AMD Radeon RX 7900 XTX",
        "AMD Radeon RX 7900 XT",
        "AMD Radeon RX 7900 GRE",
        "AMD Radeon RX 7800 XT",
        "AMD Radeon RX 7700 XT",
        "AMD Radeon RX 7600",
        # 6000-серия
        "AMD Radeon RX 6950 XT",
        "AMD Radeon RX 6900 XT",
        "AMD Radeon RX 6800 XT",
        "AMD Radeon RX 6800",
        "AMD Radeon RX 6750 XT",
        "AMD Radeon RX 6700 XT",
        "AMD Radeon RX 6650 XT",
        "AMD Radeon RX 6600 XT",
        "AMD Radeon RX 6600",
        # 5000/старшие распространённые
        "AMD Radeon RX 5700 XT",
        "AMD Radeon RX 5600 XT",
        "AMD Radeon RX 580",
        "AMD Radeon RX 570",
        # iGPU (APU)
        "AMD Radeon RX Vega 11 Graphics",
        "AMD Radeon RX Vega 8 Graphics",
        # Mac (Intel Mac dGPU часто AMD)
        "AMD Radeon Pro 560X",
        "AMD Radeon Pro 5500M",
        "AMD Radeon Pro 5300M",
    ],
    "Apple": [
        # Apple Silicon
        "Apple M3 Max",
        "Apple M3 Pro",
        "Apple M3",
        "Apple M2 Ultra",
        "Apple M2 Max",
        "Apple M2 Pro",
        "Apple M2",
        "Apple M1 Ultra",
        "Apple M1 Max",
        "Apple M1 Pro",
        "Apple M1",
    ],
}

# ANGLE renderer шаблоны под Windows (D3D11)
def build_angle_renderer_windows(vendor: str, model: str) -> str:
    if vendor == "Intel":
        return f"ANGLE (Intel, {model} Direct3D11 vs_5_0 ps_5_0, D3D11)"
    if vendor == "NVIDIA":
        return f"ANGLE (NVIDIA, {model} Direct3D11 vs_5_0 ps_5_0, D3D11)"
    if vendor == "AMD":
        return f"ANGLE (AMD, {model} Direct3D11 vs_5_0 ps_5_0, D3D11)"
    # Fallback
    return f"ANGLE (Intel, Intel(R) Iris Xe Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)"


def build_renderer_for_os(os_name: str, vendor: str, model: str) -> Tuple[str, str]:
    """
    Возвращает (webgl_vendor, webgl_renderer)
    os_name: 'windows' | 'mac' | 'linux'
    """
    os_name = (os_name or "").lower()
    if os_name == "windows":
        webgl_vendor = f"Google Inc. ({vendor})"
        renderer = build_angle_renderer_windows(vendor, model)
        return webgl_vendor, renderer
    if os_name == "mac":
        # На Mac чаще видно "Apple" и рендерер по названию чипа/диски
        webgl_vendor = "Apple"
        renderer = f"Apple {model}"
        return webgl_vendor, renderer
    # Linux / прочее
    webgl_vendor = f"Google Inc. ({vendor})"
    renderer = f"{vendor} {model}"
    return webgl_vendor, renderer


def detect_os_from_ua(ua: str) -> str:
    u = (ua or "").lower()
    if "windows nt" in u:
        return "windows"
    if "mac os x" in u:
        return "mac"
    if "linux" in u:
        return "linux"
    return "windows"


def default_platform_for_os(os_name: str) -> str:
    os_name = (os_name or "").lower()
    if os_name == "mac":
        return "MacIntel"
    if os_name == "linux":
        return "Linux x86_64"
    return "Win32"


def pick_gpu_model(vendor: str) -> str:
    models = GPU_MODELS.get(vendor, [])
    if not models:
        return "Intel(R) Iris Xe Graphics"
    return random.choice(models)


def pick_vendor_for_os(os_name: str) -> str:
    if os_name == "mac":
        # Для mac по умолчанию — Apple Silicon (можно расширить при желании под AMD dGPU)
        return "Apple"
    # На Windows/Linux наиболее частые: Intel iGPU, затем NVIDIA, затем AMD
    return random.choices(["Intel", "NVIDIA", "AMD"], weights=[0.5, 0.3, 0.2], k=1)[0]