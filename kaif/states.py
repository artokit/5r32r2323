from aiogram.dispatcher.filters.state import StatesGroup, State


class EnterAmount(StatesGroup):
    enter = State()
    select_payment = State()


class BuyProduct(StatesGroup):
    select_city = State()
    select_product = State()
    select_count = State()
    select_area = State()


class GetComments(StatesGroup):
    next_comments = State()


class ExchangeCard(StatesGroup):
    exchange_select = State()
    check_payment = State()
