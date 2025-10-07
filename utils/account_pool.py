# utils/account_pool.py
import asyncio
from db import remove_account  # Убедись, что эта функция есть в db.py


class AccountPool:
    def __init__(self, accounts):
        self._accounts = list(accounts)
        self._busy = set()
        self._lock = asyncio.Lock()

    async def take(self):
        async with self._lock:
            for acc in self._accounts:
                if acc[0] not in self._busy:
                    self._busy.add(acc[0])
                    return acc
            return None

    async def release(self, acc):
        async with self._lock:
            if not any(a[0] == acc[0] for a in self._accounts):
                # print(f"Release: аккаунта {acc[1]} уже нет в пуле, skip")
                return
            self._busy.discard(acc[0])
            # print(f"Release: {acc[1]} освобождён")

    async def ban(self, acc):
        acc_id = acc[0]
        async with self._lock:
            self._busy.discard(acc_id)
            # Удаляем из локального пула только если есть
            if any(a[0] == acc_id for a in self._accounts):
                self._accounts = [a for a in self._accounts if a[0] != acc_id]
                # print(f"Ban: {acc[1]} удалён из пула")
            else:
                # print(f"Ban: {acc[1]} уже нет в пуле")
                return
        remove_account(acc)
        # print(f"Ban: {acc[1]} удалён из базы")

    async def is_empty(self):
        async with self._lock:
            return len(self._accounts) == 0