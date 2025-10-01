from aiogram import BaseMiddleware
from config import ALLOWED_USER_IDS

class AllowListMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user_id = getattr(event.from_user, "id", None)
        if user_id is not None and user_id not in ALLOWED_USER_IDS:
            if hasattr(event, "answer"):
                await event.answer("⛔️ У вас нет доступа к этому боту.", show_alert=True)
            elif hasattr(event, "reply"):
                await event.reply("⛔️ У вас нет доступа к этому боту.")
            return
        return await handler(event, data)