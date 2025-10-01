# bot.py
import asyncio
import logging
import sys
import contextlib
from stop import AllowListMiddleware
from aiogram import Bot, Dispatcher, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

logging.getLogger('aiogram.dispatcher').setLevel(logging.CRITICAL)
logging.getLogger('aiogram').setLevel(logging.CRITICAL)
logging.getLogger('asyncio').setLevel(logging.CRITICAL)

logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from handlers.main_menu import router as main_router, cmd_start  # Импортируем функцию cmd_start
from handlers.proxy_accounts import router as proxy_accounts_router
# from handlers.platforms import router as platforms_router  # УДАЛЕНО: подключаем его через main_menu
from handlers.settings import router as settings_router
from config import BOT_TOKEN, ADMIN_IDS
from db import init_db

# --- НОВОЕ: Импорт для автозапуска ---
import handlers.main_menu as main_menu_module
# --- КОНЕЦ НОВОГО ---


async def on_startup(bot: Bot):
    startup_text = (
        "✅ <b>Бот успешно запущен!</b>\n"
        "🟢 Система готова к работе.\n"
        "📅 <b>Время запуска:</b> <code>{}</code>\n"
        "🤖 <b>Версия:</b> <code>2.1.1</code>\n\n"
        "💡 Начни рассылку через меню:"
    )

    from datetime import datetime
    current_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    text = startup_text.format(current_time)

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(chat_id=admin_id, text=text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение админу {admin_id}: {e}")
            
    # --- НОВОЕ: Запуск таймера автозапуска при старте ---
    try:
        await main_menu_module.restart_auto_start_timer(bot)
        print("🚀 Таймер автозапуска инициализирован.")
    except Exception as e:
        print(f"⚠️ Ошибка при инициализации таймера автозапуска: {e}")
    # --- КОНЕЦ НОВОГО ---


async def on_shutdown(bot: Bot):
    shutdown_text = (
        "🛑 <b>Бот остановлен</b>\n"
        "🔴 Работа приостановлена.\n"
        "📅 <b>Время остановки:</b> <code>{}</code>"
    )

    from datetime import datetime
    current_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    text = shutdown_text.format(current_time)

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(chat_id=admin_id, text=text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление админу {admin_id}: {e}")
            try:
                import requests
                url = f"https://api.telegram.org/bot{bot.token}/sendMessage"
                data = {
                    "chat_id": admin_id,
                    "text": "🛑 Бот остановлен (уведомление отправлено через API)",
                    "parse_mode": "HTML"
                }
                requests.post(url, data=data)
            except Exception as api_error:
                logger.error(f"Ошибка при отправке через API для {admin_id}: {api_error}")

# Глобальный обработчик команды /start для сброса состояний FSM
async def handle_start_command(message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        logger.warning(f"Состояние FSM сброшено из-за команды /start. Предыдущее состояние: {current_state}")
    await cmd_start(message, state)

async def main():
    try:
        init_db()
        print("✅ База данных инициализирована")

        bot = Bot(token=BOT_TOKEN)
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        dp.message.middleware(AllowListMiddleware())
        dp.callback_query.middleware(AllowListMiddleware())

        dp.message.register(handle_start_command, F.text == "/start")

        dp.include_router(main_router)
        dp.include_router(proxy_accounts_router)
        # dp.include_router(platforms_router)  # УДАЛЕНО: уже подключён внутри main_menu
        dp.include_router(settings_router)

        dp.startup.register(on_startup)
        dp.shutdown.register(on_shutdown)

        print("🚀 Запуск бота...")
        print("🤖 Бот запущен и готов к работе")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске бота: {e}", exc_info=True)
        try:
            temp_bot = Bot(token=BOT_TOKEN)
            error_msg = f"🚨 Критическая ошибка при запуске бота: {str(e)}"
            for admin_id in ADMIN_IDS:
                try:
                    await temp_bot.send_message(chat_id=admin_id, text=error_msg)
                except:
                    pass
            await temp_bot.session.close()
        except:
            pass
    finally:
        print("🛑 Работа бота завершена.")


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())