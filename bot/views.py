from django.shortcuts import render
import time
from aiogram import executor, Dispatcher, Bot
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Text
from aiogram.types import Message
from kaif import keyboards
import threading
from .models import *


bot = Bot('6133262620:AAHlfxP8Xj4ggkeDdU8OzmKZPilipkj6Ess')
dp = Dispatcher(bot, storage=MemoryStorage())


@dp.message_handler(commands=['start'])
@dp.message_handler(Text('Назад'))
@dp.message_handler(Text('В главное меню'))
async def start(message: Message):
    with open('hello.txt', 'rb') as f:
        await message.answer(f.read().decode(), reply_markup=keyboards.start)


@dp.message_handler(Text('Пополнить баланс'))
async def get_balance(message: Message):
    await message.answer(
        'Ваш баланс:  0 RUB / 0.00 BTC / 0.00 LTC\n'
        'Введите сумму для пополнения в RUB. Минимум для пополнения - 100 RUB',
        reply_markup=keyboards.balance
    )


@dp.message_handler(Text('Инъекции'))
async def injection(message: Message):
    await message.answer('https://telegra.ph/Vnutrivennyj-priem-narkotikov-05-15-2', reply_markup=keyboards.injection)


@dp.message_handler(Text('Помощь'))
async def get_help(message: Message):
    await message.answer('@Tigr_lip', reply_markup=keyboards.assistance)


@dp.message_handler(commands='otzivi')
async def get_comments(message: Message):
    await message.answer(
        ''
    )

executor.Executor(dp).start_polling()
