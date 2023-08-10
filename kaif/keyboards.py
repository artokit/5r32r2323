from aiogram.types import *
from bot.models import PaymentCrypto
from asgiref.sync import sync_to_async


@sync_to_async
def keyboard_builder(data: list, key):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    while data:
        arr = data[:3]
        data = data[3:]

        if key == '__str__':
            keyboard.add(*[KeyboardButton(str(i)) for i in arr])
        else:
            keyboard.add(*[KeyboardButton(i.__getattribute__(key)) for i in arr])

    keyboard.add(KeyboardButton('Инъекции'))
    keyboard.add(KeyboardButton('В главное меню'), KeyboardButton('Прайс'), KeyboardButton('Помощь'))

    return keyboard


start = ReplyKeyboardMarkup(resize_keyboard=True)
start.add(KeyboardButton('Пополнить баланс'), KeyboardButton('Совершить покупку'))
start.add(KeyboardButton('Инъекции'))
start.add(KeyboardButton('В главное меню'), KeyboardButton('Прайс'), KeyboardButton('Помощь'))

balance = ReplyKeyboardMarkup(resize_keyboard=True)
balance.add(KeyboardButton('Назад'))
balance.add(KeyboardButton('Инъекции'))
balance.add(KeyboardButton('В главное меню'), KeyboardButton('Прайс'), KeyboardButton('Помощь'))

injection = ReplyKeyboardMarkup(resize_keyboard=True)
injection.add(KeyboardButton('Инъекции'))
injection.add(KeyboardButton('В главное меню'), KeyboardButton('Прайс'), KeyboardButton('Помощь'))

assistance = injection

payments = PaymentCrypto.objects.all()
payments_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
payments_keyboard.add(*[KeyboardButton(payment.title) for payment in payments], KeyboardButton('Visa/MasterCard'))
payments_keyboard.add(KeyboardButton('Инъекции'))
payments_keyboard.add(KeyboardButton('В главное меню'), KeyboardButton('Прайс'), KeyboardButton('Помощь'))

buy = ReplyKeyboardMarkup(resize_keyboard=True)
buy.add(KeyboardButton('💰Проверить оплату💰'), KeyboardButton('Совершить покупку'))
buy.add(KeyboardButton('Инъекции'))
buy.add(KeyboardButton('В главное меню'), KeyboardButton('Прайс'), KeyboardButton('Помощь'))

after_select_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
after_select_keyboard.add(KeyboardButton('💰Проверить оплату💰'))
after_select_keyboard.add(KeyboardButton('Инъекции'))
after_select_keyboard.add(KeyboardButton('В главное меню'), KeyboardButton('Прайс'), KeyboardButton('Помощь'))

check_exchange = ReplyKeyboardMarkup(resize_keyboard=True)
check_exchange.add(KeyboardButton('Проверить оплату'), KeyboardButton('Отменить оплату'))
check_exchange.add(KeyboardButton('Инъекции'))
check_exchange.add(KeyboardButton('В главное меню'), KeyboardButton('Прайс'), KeyboardButton('Помощь'))
