from aiogram.fsm.state import State, StatesGroup

class AccountsStates(StatesGroup):
    waiting_for_accounts = State()

class CookieStates(StatesGroup):
    waiting_for_cookie_file = State()