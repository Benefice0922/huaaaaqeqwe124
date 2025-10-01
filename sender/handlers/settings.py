from __future__ import annotations

import io
import re
from typing import List

from aiogram import Router, F, types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db import get_settings, set_setting
from keyboards.settings import (
    get_settings_menu,
    get_common_menu,
    get_autostart_menu,
    get_fingerprint_menu,
    get_resolution_menu,
    get_hardware_menu,
    get_back_menu,
)

router = Router()
router.event_types = {"message", "callback_query"}

class SettingsFSM(StatesGroup):
    waiting_for_timer = State()
    waiting_for_ua_file = State()
    waiting_for_custom_resolution = State()

def build_root_caption(s: dict) -> str:
    visible = "👁️ Видим" if s.get("browser_visible") else "🙈 Скрыт"
    no_proxy = "✅" if s.get("without_proxy") else "❌"
    no_acc = "✅" if s.get("without_accounts") else "❌"
    timer = s.get("autostart_timer")
    timer_txt = f"{timer} сек." if timer else "Отключен"
    ua_source = s.get("ua_source", "random")
    ua_count = int(s.get("ua_count", 0))
    ua_txt = "🎲 Рандом" if ua_source != "file" else f"📁 Файл ({ua_count})"
    res_txt = s.get("screen_resolution") if (s.get("screen_resolution") and not s.get("random_resolution", True)) else "🎲 Рандом (ПК ≥1440×900)"
    hw_src = s.get("hw_source", "auto")
    return (
        "⚙️ <b>Настройки</b>\n\n"
        "🕵️ <b>Антидетект</b>\n"
        f"• UA: <code>{ua_txt}</code>\n"
        f"• Разрешение: <code>{res_txt}</code>\n"
        f"• Устройство: <code>{'Авто' if hw_src=='auto' else 'Кастом'}</code>\n\n"
        "⚙️ <b>Общие</b>\n"
        f"• Видимость браузера: <code>{visible}</code>\n"
        f"• Без прокси: <code>{no_proxy}</code> | Без аккаунтов: <code>{no_acc}</code>\n\n"
        "⏱ <b>Автозапуск</b>\n"
        f"• Таймер: <code>{timer_txt}</code>"
    )

def build_autostart_caption(s: dict) -> str:
    t = s.get("autostart_timer")
    ttxt = f"{t} сек." if t else "Отключен"
    return "⏱ <b>Автозапуск</b>\nТекущее значение: <code>{}</code>\n\nВыберите пресет или введите своё значение в секундах.".format(ttxt)

def build_fingerprint_caption(s: dict) -> str:
    ua_source = s.get("ua_source", "random")
    ua_count = int(s.get("ua_count", 0))
    ua_txt = "🎲 Рандом" if ua_source != "file" else f"📁 Файл ({ua_count})"
    res_txt = s.get("screen_resolution") if (s.get("screen_resolution") and not s.get("random_resolution", True)) else "🎲 Рандом (ПК ≥1440×900)"
    hw_src = s.get("hw_source", "auto")
    return (
        "🕵️ <b>Антидетект</b>\n"
        f"• Источник UA: <code>{ua_txt}</code>\n"
        f"• Разрешение: <code>{res_txt}</code>\n"
        f"• Устройство: <code>{'Авто' if hw_src=='auto' else 'Кастом'}</code>\n\n"
        "Загрузите файл UA / переключите источник, настройте разрешение и устройство."
    )

@router.callback_query(F.data == "settings")
async def show_settings(callback: types.CallbackQuery):
    s = get_settings()
    await callback.answer()
    await callback.message.edit_text(build_root_caption(s), reply_markup=get_settings_menu(s), parse_mode="HTML")

@router.callback_query(F.data == "settings_back_root")
async def settings_back_root(callback: types.CallbackQuery):
    s = get_settings()
    await callback.answer()
    await callback.message.edit_text(build_root_caption(s), reply_markup=get_settings_menu(s), parse_mode="HTML")

@router.callback_query(F.data == "open_common_settings")
async def open_common_settings(callback: types.CallbackQuery):
    await callback.answer()
    s = get_settings()
    await callback.message.edit_text("⚙️ <b>Общие настройки</b>\nВыберите, что включить/выключить:", reply_markup=get_common_menu(s), parse_mode="HTML")

@router.callback_query(F.data == "open_autostart_settings")
async def open_autostart_settings(callback: types.CallbackQuery):
    await callback.answer()
    s = get_settings()
    await callback.message.edit_text(build_autostart_caption(s), reply_markup=get_autostart_menu(s), parse_mode="HTML")

@router.callback_query(F.data == "open_fingerprint_settings")
async def open_fingerprint_settings(callback: types.CallbackQuery):
    s = get_settings()
    await callback.answer()
    await callback.message.edit_text(build_fingerprint_caption(s), reply_markup=get_fingerprint_menu(s), parse_mode="HTML")

@router.callback_query(F.data == "back_to_fingerprint")
async def back_to_fingerprint(callback: types.CallbackQuery):
    await open_fingerprint_settings(callback)

@router.callback_query(F.data == "noop")
async def noop(callback: types.CallbackQuery):
    await callback.answer()

# Общие тумблеры
@router.callback_query(F.data == "toggle_browser_visible")
async def toggle_browser_visible(callback: types.CallbackQuery):
    s = get_settings(); s['browser_visible'] = not s.get('browser_visible', False)
    set_setting('browser_visible', s['browser_visible'])
    await callback.answer(f"Видимость: {'Включена' if s['browser_visible'] else 'Отключена'}")
    await callback.message.edit_reply_markup(reply_markup=get_common_menu(s))

@router.callback_query(F.data == "toggle_without_proxy")
async def toggle_without_proxy(callback: types.CallbackQuery):
    s = get_settings(); s['without_proxy'] = not s.get('without_proxy', False)
    set_setting('without_proxy', s['without_proxy'])
    await callback.answer(f"Без прокси: {'Вкл' if s['without_proxy'] else 'Выкл'}")
    await callback.message.edit_reply_markup(reply_markup=get_common_menu(s))

@router.callback_query(F.data == "toggle_without_accounts")
async def toggle_without_accounts(callback: types.CallbackQuery):
    s = get_settings(); s['without_accounts'] = not s.get('without_accounts', False)
    set_setting('without_accounts', s['without_accounts'])
    await callback.answer(f"Без аккаунтов: {'Вкл' if s['without_accounts'] else 'Выкл'}")
    await callback.message.edit_reply_markup(reply_markup=get_common_menu(s))

# Автозапуск
@router.callback_query(F.data == "set_autostart_timer")
async def set_autostart_timer(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text("Укажите время автозапуска в секундах (0 для отключения):", reply_markup=get_back_menu())
    await state.set_state(SettingsFSM.waiting_for_timer)

@router.callback_query(F.data.startswith("set_autostart_preset:"))
async def set_autostart_preset(callback: types.CallbackQuery):
    _, val = callback.data.split(":", 1)
    secs = int(val) if val.isdigit() else 0
    set_setting("autostart_timer", secs if secs > 0 else None)
    await callback.answer(f"Таймер: {secs if secs > 0 else 'Отключен'}")
    s = get_settings()
    await callback.message.edit_text(build_autostart_caption(s), reply_markup=get_autostart_menu(s), parse_mode="HTML")
    try:
        import handlers.main_menu as main_menu_module
        await main_menu_module.restart_auto_start_timer(callback.bot)
    except Exception as e:
        print(f"[SETTINGS] Ошибка перезапуска автозапуска: {e}")

@router.message(SettingsFSM.waiting_for_timer, F.text)
async def receive_timer(message: types.Message, state: FSMContext, bot: Bot):
    try:
        timer = int(message.text.strip())
        set_setting('autostart_timer', timer if timer > 0 else None)
        s = get_settings()
        await message.answer(build_autostart_caption(s), reply_markup=get_autostart_menu(s), parse_mode="HTML")
        try:
            import handlers.main_menu as main_menu_module
            await main_menu_module.restart_auto_start_timer(bot)
        except Exception as e:
            print(f"[SETTINGS] Ошибка перезапуска таймера: {e}")
    except Exception:
        await message.answer("Ошибка! Введите число.")
    await state.clear()

# Антидетект — UA/Resolutions (часть уже была у вас)
@router.callback_query(F.data == "toggle_ua_source")
async def toggle_ua_source(callback: types.CallbackQuery):
    s = get_settings(); current = s.get("ua_source", "random")
    new_val = "file" if current != "file" else "random"
    set_setting("ua_source", new_val)
    await callback.answer(f"Источник UA: {'файл' if new_val == 'file' else 'рандом'}")
    s = get_settings()
    await callback.message.edit_text(build_fingerprint_caption(s), reply_markup=get_fingerprint_menu(s), parse_mode="HTML")

@router.callback_query(F.data == "upload_ua_file")
async def upload_ua_file(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("Пришлите .txt файл или список UA текстом.")
    await callback.message.edit_text("Пришлите .txt файл с User-Agent (каждый на новой строке) или отправьте список текстом.", reply_markup=get_back_menu())
    await state.set_state(SettingsFSM.waiting_for_ua_file)

@router.message(SettingsFSM.waiting_for_ua_file, F.document)
async def receive_ua_file_document(message: types.Message, state: FSMContext):
    from handlers.settings import _save_user_agents  # предполагается, что helper у вас уже есть
    doc = message.document
    if not doc or (doc.file_name and not doc.file_name.lower().endswith(".txt")):
        await message.answer("Нужен .txt файл.")
        return
    buf = io.BytesIO()
    await message.bot.download(doc, destination=buf)
    buf.seek(0)
    content = buf.read().decode("utf-8", errors="ignore")
    lines = [l.strip() for l in content.splitlines()]
    count = _save_user_agents(lines)
    await message.answer(f"Файл загружен. Уникальных UA: {count}", reply_markup=get_fingerprint_menu(get_settings()), parse_mode="HTML")
    await state.clear()

@router.message(SettingsFSM.waiting_for_ua_file, F.text)
async def receive_ua_file_text(message: types.Message, state: FSMContext):
    from handlers.settings import _save_user_agents
    lines = [l.strip() for l in message.text.splitlines()]
    count = _save_user_agents(lines)
    await message.answer(f"Принято. Уникальных UA: {count}", reply_markup=get_fingerprint_menu(get_settings()), parse_mode="HTML")
    await state.clear()

@router.callback_query(F.data == "toggle_random_resolution")
async def toggle_random_resolution(callback: types.CallbackQuery):
    s = get_settings(); flag = not s.get("random_resolution", True)
    set_setting("random_resolution", flag)
    await callback.answer(f"Рандомное разрешение: {'вкл' if flag else 'выкл'}")
    s = get_settings()
    await callback.message.edit_text(build_fingerprint_caption(s), reply_markup=get_fingerprint_menu(s), parse_mode="HTML")

@router.callback_query(F.data == "open_resolution_menu")
async def open_resolution_menu(callback: types.CallbackQuery):
    s = get_settings()
    await callback.answer()
    await callback.message.edit_text("<b>Выбор разрешения экрана</b>\nПК-пресеты (≥1440×900) или введите своё.", reply_markup=get_resolution_menu(s.get("screen_resolution"), s.get("random_resolution", True)), parse_mode="HTML")

@router.callback_query(F.data.startswith("set_resolution:"))
async def set_resolution(callback: types.CallbackQuery):
    _, value = callback.data.split(":", 1)
    if value == "random":
        set_setting("random_resolution", True); set_setting("screen_resolution", None)
        await callback.answer("Режим рандома включён.")
    else:
        if not re.fullmatch(r"\d{2,4}x\d{2,4}", value):
            await callback.answer("Неверный формат.")
            return
        set_setting("random_resolution", False); set_setting("screen_resolution", value)
        await callback.answer(f"Разрешение: {value}")
    s = get_settings()
    await callback.message.edit_text("<b>Выбор разрешения экрана</b>\nПК-пресеты (≥1440×900) или введите своё.", reply_markup=get_resolution_menu(s.get("screen_resolution"), s.get("random_resolution", True)), parse_mode="HTML")

@router.callback_query(F.data == "enter_custom_resolution")
async def enter_custom_resolution(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text("Введите разрешение в формате ШxВ, например 1920x1080", reply_markup=get_back_menu())
    await state.set_state(SettingsFSM.waiting_for_custom_resolution)

@router.message(SettingsFSM.waiting_for_custom_resolution, F.text)
async def receive_custom_resolution(message: types.Message, state: FSMContext):
    text = message.text.strip().lower().replace(" ", "")
    m = re.fullmatch(r"(\d{2,4})x(\d{2,4})", text)
    if not m:
        await message.answer("Неверный формат. Пример: 1920x1080")
        return
    w, h = int(m.group(1)), int(m.group(2))
    set_setting("random_resolution", False); set_setting("screen_resolution", f"{w}x{h}")
    await message.answer("🕵️ Возврат в антидетект", reply_markup=get_fingerprint_menu(get_settings()), parse_mode="HTML")
    await state.clear()

# Антидетект — Устройство
@router.callback_query(F.data == "open_hardware_settings")
async def open_hardware_settings(callback: types.CallbackQuery):
    s = get_settings()
    await callback.answer()
    await callback.message.edit_text("🧠 <b>Устройство</b>\nНастройте GPU/шумы/платформу/CPU/память.", reply_markup=get_hardware_menu(s), parse_mode="HTML")

@router.callback_query(F.data == "toggle_hw_source")
async def toggle_hw_source(callback: types.CallbackQuery):
    s = get_settings(); cur = s.get("hw_source", "auto")
    newv = "custom" if cur == "auto" else "auto"
    set_setting("hw_source", newv)
    await callback.answer(f"Источник: {newv}")
    await callback.message.edit_reply_markup(reply_markup=get_hardware_menu(get_settings()))

@router.callback_query(F.data == "cycle_hw_gpu_vendor")
async def cycle_hw_gpu_vendor(callback: types.CallbackQuery):
    order = ["auto", "Intel", "NVIDIA", "AMD", "Apple"]
    s = get_settings(); cur = s.get("hw_gpu_vendor", "auto")
    nxt = order[(order.index(cur) + 1) % len(order)] if cur in order else "Intel"
    set_setting("hw_gpu_vendor", nxt)
    # при смене вендора сбросим модель в auto
    set_setting("hw_gpu_model", "auto")
    await callback.answer(f"GPU вендор: {nxt}")
    await callback.message.edit_reply_markup(reply_markup=get_hardware_menu(get_settings()))

@router.callback_query(F.data == "cycle_hw_gpu_model")
async def cycle_hw_gpu_model(callback: types.CallbackQuery):
    # Модели прокликиваются между auto -> список 3-4 моделей
    from utils.device_profiles import GPU_MODELS
    s = get_settings()
    vendor = s.get("hw_gpu_vendor", "auto")
    if vendor == "auto":
        await callback.answer("Сначала выберите вендора.")
        return
    models = ["auto"] + (GPU_MODELS.get(vendor, []) or [])
    cur = s.get("hw_gpu_model", "auto")
    try:
        idx = models.index(cur)
    except ValueError:
        idx = 0
    nxt = models[(idx + 1) % len(models)]
    set_setting("hw_gpu_model", nxt)
    await callback.answer(f"Модель: {nxt}")
    await callback.message.edit_reply_markup(reply_markup=get_hardware_menu(get_settings()))

@router.callback_query(F.data == "cycle_hw_noise")
async def cycle_hw_noise(callback: types.CallbackQuery):
    order = ["low", "medium", "high"]
    s = get_settings(); cur = s.get("hw_noise_level", "medium")
    nxt = order[(order.index(cur) + 1) % len(order)] if cur in order else "medium"
    set_setting("hw_noise_level", nxt)
    await callback.answer(f"Шум: {nxt}")
    await callback.message.edit_reply_markup(reply_markup=get_hardware_menu(get_settings()))

@router.callback_query(F.data == "cycle_hw_hc")
async def cycle_hw_hc(callback: types.CallbackQuery):
    order = ["auto", "8", "12", "16", "20"]
    s = get_settings(); cur = str(s.get("hw_hc", "auto"))
    nxt = order[(order.index(cur) + 1) % len(order)] if cur in order else "8"
    set_setting("hw_hc", None if nxt == "auto" else int(nxt))
    await callback.answer(f"CPU threads: {nxt}")
    await callback.message.edit_reply_markup(reply_markup=get_hardware_menu(get_settings()))

@router.callback_query(F.data == "cycle_hw_mem")
async def cycle_hw_mem(callback: types.CallbackQuery):
    order = ["auto", "8", "16", "32"]
    s = get_settings(); cur = str(s.get("hw_mem", "auto"))
    nxt = order[(order.index(cur) + 1) % len(order)] if cur in order else "16"
    set_setting("hw_mem", None if nxt == "auto" else int(nxt))
    await callback.answer(f"Memory: {nxt}")
    await callback.message.edit_reply_markup(reply_markup=get_hardware_menu(get_settings()))

@router.callback_query(F.data == "cycle_hw_platform")
async def cycle_hw_platform(callback: types.CallbackQuery):
    order = ["auto", "Win32", "MacIntel"]
    s = get_settings(); cur = s.get("hw_platform_override", "auto")
    nxt = order[(order.index(cur) + 1) % len(order)] if cur in order else "Win32"
    set_setting("hw_platform_override", nxt)
    await callback.answer(f"Платформа: {nxt}")
    await callback.message.edit_reply_markup(reply_markup=get_hardware_menu(get_settings()))

@router.callback_query(F.data == "toggle_hw_mtp")
async def toggle_hw_mtp(callback: types.CallbackQuery):
    s = get_settings(); cur = int(s.get("hw_max_touch_points", 0) or 0)
    nxt = 0 if cur != 0 else 1
    set_setting("hw_max_touch_points", nxt)
    await callback.answer(f"maxTouchPoints: {nxt}")
    await callback.message.edit_reply_markup(reply_markup=get_hardware_menu(get_settings()))

@router.callback_query(F.data == "cycle_hw_cdepth")
async def cycle_hw_cdepth(callback: types.CallbackQuery):
    order = [24, 30]
    s = get_settings(); cur = int(s.get("hw_color_depth", 24) or 24)
    nxt = order[(order.index(cur) + 1) % len(order)]
    set_setting("hw_color_depth", int(nxt))
    await callback.answer(f"ColorDepth: {nxt}")
    await callback.message.edit_reply_markup(reply_markup=get_hardware_menu(get_settings()))

@router.callback_query(F.data == "toggle_text_rotation")
async def toggle_text_rotation(callback: types.CallbackQuery):
    s = get_settings()
    s['text_rotation'] = not s.get('text_rotation', False)
    set_setting('text_rotation', s['text_rotation'])
    await callback.answer(f"Ротация текстов: {'Вкл' if s['text_rotation'] else 'Выкл'}")
    await callback.message.edit_reply_markup(reply_markup=get_common_menu(s))