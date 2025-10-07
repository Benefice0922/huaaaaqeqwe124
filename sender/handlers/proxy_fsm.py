from aiogram.fsm.state import State, StatesGroup

class ProxyStates(StatesGroup):
    waiting_for_proxies = State()