import asyncio
from typing import Dict, Optional, Set, Any

class AccountStatusManager:
    """
    Менеджер статусов аккаунтов, совместимый с вызовами из krisha_worker.py и kolesa_worker.py.

    Хранит:
      - статус по имени аккаунта (banned, ban_reason, ban_worker_id)
      - маппинг worker_id -> (account_name, task)
      - обратное соответствие account_name -> set(worker_id)
    """
    def __init__(self):
        self._lock = asyncio.Lock()
        self._accounts: Dict[str, Dict[str, Any]] = {}
        self._workers: Dict[Any, Dict[str, Any]] = {}
        self._account_workers: Dict[str, Set[Any]] = {}

    # --- ВСПОМОГАТЕЛЬНОЕ ---

    def _ensure_account(self, account_name: Optional[str]) -> Dict[str, Any]:
        if not account_name:
            # Для "Без аккаунта" тоже возвращаем валидный статус
            account_name = "Без аккаунта"
        if account_name not in self._accounts:
            self._accounts[account_name] = {
                "banned": False,
                "ban_reason": None,
                "ban_worker_id": None,
            }
        return self._accounts[account_name]

    # --- ПУБЛИЧНЫЙ API, КОТОРЫЙ ЖДУТ ВОРКЕРЫ ---

    async def register_worker(self, worker_id: Any, account_name: str, task: asyncio.Task) -> Dict[str, Any]:
        """
        Регистрирует воркера и возвращает текущий статус аккаунта.
        Совместимо с вызовами:
            await account_manager.register_worker(worker_id, username, current_task)
        """
        async with self._lock:
            status = self._ensure_account(account_name)
            # Привяжем воркер к аккаунту
            self._workers[worker_id] = {"account_name": account_name, "task": task}
            self._account_workers.setdefault(account_name, set()).add(worker_id)
            # Если аккаунт уже помечен забаненным — вернём это сразу
            return dict(status)

    async def unregister_worker(self, worker_id: Any, account_name: Optional[str] = None, task: Optional[asyncio.Task] = None):
        """
        Совместимо с вызовами:
            await account_manager.unregister_worker(worker_id, username, current_task)
        Параметры account_name и task допускаются и игнорируются (для совместимости).
        """
        async with self._lock:
            # Определим аккаунт по worker_id, если не передан
            if worker_id in self._workers:
                acc = self._workers[worker_id].get("account_name")
            else:
                acc = account_name
            # Удалим воркер
            self._workers.pop(worker_id, None)
            if acc:
                workers = self._account_workers.get(acc)
                if workers and worker_id in workers:
                    workers.remove(worker_id)
                if workers and len(workers) == 0:
                    # Оставляем статус аккаунта (может пригодиться позже), чистим только список воркеров
                    self._account_workers.pop(acc, None)

    async def get_account_status(self, account_name: str) -> Dict[str, Any]:
        """
        Совместимо с krisha_worker:
            acc_status = await account_manager.get_account_status(username)
        """
        async with self._lock:
            return dict(self._ensure_account(account_name))

    async def is_account_banned(self, account_name: str) -> bool:
        """
        Совместимо с kolesa_worker:
            if await account_manager.is_account_banned(username):
        """
        async with self._lock:
            return bool(self._ensure_account(account_name).get("banned"))

    async def mark_banned(self, account_name: str, worker_id: Optional[Any] = None, reason: str = "unknown"):
        """
        Совместимо с krisha_worker:
            await account_manager.mark_banned(username, worker_id, "restricted")
        """
        async with self._lock:
            status = self._ensure_account(account_name)
            status["banned"] = True
            status["ban_reason"] = reason
            status["ban_worker_id"] = worker_id

    async def set_account_banned(self, account_name: str, reason: str = "unknown"):
        """
        Совместимо с kolesa_worker:
            await account_manager.set_account_banned(username, "invalid_credentials")
        """
        await self.mark_banned(account_name, worker_id=None, reason=reason)

    # --- СТАРЫЕ/ДОП. МЕТОДЫ ДЛЯ СОВМЕСТИМОСТИ (если вдруг где-то используются) ---

    def clear_all(self):
        self._accounts.clear()
        self._workers.clear()
        self._account_workers.clear()

    # Для старого кода: get_worker_status(worker_id)
    def get_worker_status(self, worker_id: Any) -> Optional[Dict[str, Any]]:
        """
        Возвращает статус аккаунта, к которому привязан воркер.
        """
        info = self._workers.get(worker_id)
        if not info:
            return None
        acc = info.get("account_name")
        if not acc:
            return None
        return dict(self._accounts.get(acc, {}))


# Глобальный экземпляр
account_manager = AccountStatusManager()