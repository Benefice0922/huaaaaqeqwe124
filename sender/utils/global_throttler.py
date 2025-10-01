import asyncio
import time
import os

GLOBAL_THROTTLE_FILE = 'global_throttle.lock'
MIN_DELAY = 2  # секунд между отправками глобально

async def global_throttle():
    now = time.time()
    last_time = 0
    if os.path.exists(GLOBAL_THROTTLE_FILE):
        try:
            with open(GLOBAL_THROTTLE_FILE, 'r') as f:
                last_time = float(f.read().strip())
        except Exception:
            last_time = 0
    wait_time = max(0, MIN_DELAY - (now - last_time))
    if wait_time > 0:
        await asyncio.sleep(wait_time)
    with open(GLOBAL_THROTTLE_FILE, 'w') as f:
        f.write(str(time.time()))