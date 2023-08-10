import asyncio
import os.path
import random
from asgiref.sync import sync_to_async
from django.core import paginator
from aiogram.dispatcher import FSMContext
from django.core.management.base import BaseCommand
from bot.models import *
from aiogram import executor
from aiogram.dispatcher.filters import Text
from aiogram.types import Message
from kaif import keyboards
from kaif.settings import dp
import requests
from kaif import states

HELLO_TEXT_PATH = os.path.join(os.path.dirname(__file__), 'hello.txt')
CRYPTO_PAYMENTS = PaymentCrypto.objects.all()
PAYMENTS = [i.title for i in CRYPTO_PAYMENTS]


async def get_user_balance_in_text(user_id):
    user = (await TelegramUser.objects.aget_or_create(user_id=user_id))[0]
    course = get_course(user.balance)
    return f'Ваш баланс:  {course["rub"]} RUB / {course["btc"]} BTC / {course["ltc"]} LTC'


def get_course(count_of_money):
    if count_of_money:
        ltc_course = requests.get('https://apirone.com/api/v2/ticker?currency=ltc').json()['rub']
        btc_course = requests.get('https://apirone.com/api/v2/ticker?currency=btc').json()['rub']
        return {
            'rub': count_of_money,
            'btc': round(count_of_money / btc_course, 8),
            'ltc': round(count_of_money / ltc_course, 8)
        }
    return {i: 0 for i in ['rub', 'btc', 'ltc']}


@dp.message_handler(commands=['otziv'])
async def comment(message: Message):
    await message.answer(
        'Отзывы можно оставлять только после покупок',
        reply_markup=keyboards.injection
    )


@dp.message_handler(commands=['start'], state='*')
@dp.message_handler(Text('Назад'), state='*')
@dp.message_handler(Text('В главное меню'), state='*')
async def start(message: Message, state: FSMContext):
    await state.reset_data()
    await state.finish()
    user = (await TelegramUser.objects.aget_or_create(user_id=message.chat.id, username=message.chat.username))[0]
    with open(HELLO_TEXT_PATH, 'rb') as f:
        text = f.read().decode()

        course = get_course(user.balance)
        text = text.replace(
            'BALANCE', str(course['rub']), 1
        ).replace(
            'BTC_BALANCE', str(course['btc'])
        ).replace(
            'LTC_BALANCE', str(course['ltc'])
        )

        await message.answer(
            text,
            reply_markup=keyboards.start
        )


@dp.message_handler(Text('Пополнить баланс'))
async def get_balance(message: Message):
    user = (await TelegramUser.objects.aget_or_create(user_id=message.chat.id, username=message.chat.username))[0]
    course = get_course(user.balance)

    await states.EnterAmount.enter.set()
    await message.answer(
        f'Ваш баланс:  {course["rub"]} RUB / {course["btc"]} BTC / {course["ltc"]} LTC\n'
        'Введите сумму для пополнения в RUB. Минимум для пополнения - 100 RUB',
        reply_markup=keyboards.balance
    )


@dp.message_handler(state=states.EnterAmount.enter)
async def enter_amount(message: Message, state: FSMContext):
    if message.text.isdigit():
        amount = int(message.text)
        if amount < 100:
            return await message.answer('Введите сумму для пополнения в RUB. Минимум для пополнения - 100 RUB')
        user = await TelegramUser.objects.aget(user_id=message.chat.id)
        course = get_course(user.balance)

        await states.EnterAmount.select_payment.set()
        await state.set_data({'amount': amount})

        return await message.answer(
            f'<b>Ваш баланс:</b>  {course["rub"]} RUB / {course["btc"]} BTC / {course["ltc"]} LTC\n\n\n\n'
            f'<b>Выберите способ оплаты:</b>',
            parse_mode='html',
            reply_markup=keyboards.payments_keyboard
        )

    await message.answer('Введите сумму для пополнения в RUB. Минимум для пополнения - 100 RUB')


@dp.message_handler(Text('Инъекции'), state='*')
async def injection(message: Message, state: FSMContext):
    await state.reset_data()
    await state.finish()
    await message.answer('https://telegra.ph/Vnutrivennyj-priem-narkotikov-05-15-2', reply_markup=keyboards.injection)


@dp.message_handler(Text('Помощь'), state='*')
async def get_help(message: Message, state: FSMContext):
    await state.reset_data()
    await state.finish()
    await message.answer('@Tigr_lip', reply_markup=keyboards.assistance)


@dp.message_handler(commands='otzivi', state='*')
async def get_comments(message: Message, state=FSMContext):
    await states.GetComments.next_comments.set()
    num_page = (await state.get_data()).get('page', 1)

    try:
        page = await get_comments_page(num_page)
    except paginator.EmptyPage:
        await state.set_data({'page': 1})
        return await get_comments(message, state)

    text = ''

    async for com in page:
        text += f'➖➖От {com.nickname} {com.date}➖➖\n' \
               f'{com.content}\n\n'

    await state.update_data({'page': num_page + 1})
    await message.answer(
        'Показать еще (нажмите 👉 /otzivi)\n\n' + text,
        reply_markup=keyboards.injection
    )


@sync_to_async
def get_comments_page(num_page):
    comments = paginator.Paginator(Comment.objects.all(), 5)
    return comments.page(num_page).object_list


@dp.message_handler(Text('Совершить покупку'), state='*')
async def buy_product(message: Message):
    user = await TelegramUser.objects.aget(user_id=message.chat.id)
    course = get_course(user.balance)

    await states.BuyProduct.select_city.set()

    await message.answer(
        f'<b>Ваш баланс:</b>  {course["rub"]} RUB / {course["btc"]} BTC / {course["ltc"]} LTC\n\n'
        '<b>Для покупки нажмите на свой город внизу:</b>',
        parse_mode='html',
        reply_markup=await keyboards.keyboard_builder(City.objects.all(), 'name')
    )


@dp.message_handler(lambda message: message.text in PAYMENTS, state=states.EnterAmount.select_payment)
async def select_payment(message: Message, state: FSMContext):
    amount = (await state.get_data())['amount']
    title = message.text
    obj = await PaymentCrypto.objects.aget(title=title)
    after_buy = (await state.get_data()).get('buy', False)

    await state.update_data({'payment': obj})
    if obj:
        r = requests.get(f'https://apirone.com/api/v2/ticker?currency={obj.code}').json()['rub']
        st = f'{await get_user_balance_in_text(message.chat.id)}\n\n' if not after_buy else ''
        middle = '<b>Как баланс пополнится - переходите к покупкам.</b>\n' if not after_buy else ''
        await message.answer(
            st +
            f'<b>Переведите {obj.code.upper()}</b>\n' +
            middle +
            '➖➖➖➖➖➖➖➖➖➖\n'
            f'<b>Кошелек:</b> {obj.card}\n'
            f'<b>Сумма:</b> {round(amount/r, 8)} {obj.code.upper()}\n'
            f'<b>Курс:</b> {int(r)} RUB/{obj.code.upper()}\n'
            '➖➖➖➖➖➖➖➖➖➖\n'
            '<b>ЧТОБЫ ОПЛАТА БЫСТРЕЕ ЗАЧИСЛИЛАСЬ, СТАВЬТЕ ВЫСОКУЮ КОМИССИЮ</b>\n\n'
            f'Чтобы получить кошелек отдельным сообщением нажмите 👉 /my{obj.code.lower()}',
            parse_mode='html',
            reply_markup=keyboards.buy if not after_buy else keyboards.after_select_keyboard
        )

    else:
        await message.answer(
            'Неправильный выбор, попробуйте еще раз.\n'
            'Для выбора варианта нажмите на кнопку снизу'
        )


@dp.message_handler(Text('💰Проверить оплату💰'), state=states.EnterAmount.select_payment)
async def check_pay(message: Message, state: FSMContext):
    await asyncio.sleep(random.randint(5, 10))
    amount = (await state.get_data())['amount']
    obj = (await state.get_data())['payment']
    if obj:
        r = requests.get(f'https://apirone.com/api/v2/ticker?currency={obj.code}').json()['rub']

        user = await TelegramUser.objects.aget(user_id=message.chat.id)
        course = get_course(user.balance)

        await message.answer(
            f'<b>Ваш баланс:</b>  {course["rub"]} RUB / {course["btc"]} BTC / {course["ltc"]} LTC\n\n'
            f'<b>Переведите {obj.code.upper()}</b>\n'
            '<b>Как баланс пополнится - переходите к покупкам.</b>\n'
            '➖➖➖➖➖➖➖➖➖➖\n'
            f'<b>Кошелек:</b> {obj.card}\n'
            f'<b>Сумма:</b> {round(amount/r, 8)} {obj.code.upper()}\n'
            f'<b>Курс:</b> {int(r)} RUB/{obj.code.upper()}\n'
            '➖➖➖➖➖➖➖➖➖➖\n'
            '<b>ЧТОБЫ ОПЛАТА БЫСТРЕЕ ЗАЧИСЛИЛАСЬ, СТАВЬТЕ ВЫСОКУЮ КОМИССИЮ</b>\n\n'
            f'Чтобы получить кошелек отдельным сообщением нажмите 👉 /my{obj.code.lower()}',
            parse_mode='html',
            reply_markup=keyboards.buy
        )

    else:
        await message.answer(
            'Неправильный выбор, попробуйте еще раз.\n'
            'Для выбора варианта нажмите на кнопку снизу'
        )


@dp.message_handler(state=states.BuyProduct.select_city)
async def select_city(message: Message, state: FSMContext):
    try:
        city = await City.objects.aget(name=message.text)
    except City.DoesNotExist:
        return await message.answer(
            'Неправильный выбор, попробуйте еще раз.\n'
            'Для выбора варианта нажмите на кнопку снизу',
            reply_markup=await keyboards.keyboard_builder(City.objects.all(), 'name')
        )

    await state.update_data({'city': city})
    await states.BuyProduct.select_product.set()

    await message.answer(
        f'{await get_user_balance_in_text(message.chat.id)}\n\n'
        f'<b>Вы выбрали</b> "{city.name}"\n\n'
        '➖➖➖➖➖➖➖➖➖➖\n'
        f'🏡 <b>Город:</b> {city.name}\n'
        '➖➖➖➖➖➖➖➖➖➖\n\n'
        '<b>Выберите товар:</b>',
        parse_mode='html',
        reply_markup=await keyboards.keyboard_builder(Product.objects.filter(city=city), 'name')
    )


@dp.message_handler(state=states.BuyProduct.select_product)
async def select_product(message: Message, state: FSMContext):
    user_data = await state.get_data()
    city = user_data['city']
    try:
        product = await Product.objects.aget(name=message.text, city=city)
    except Product.DoesNotExist:
        return await message.answer(
            'Неправильный выбор, попробуйте еще раз.\n'
            'Для выбора варианта нажмите на кнопку снизу',
            reply_markup=await keyboards.keyboard_builder(Product.objects.filter(city=city), 'name')
        )

    await state.update_data({'product': product})
    await states.BuyProduct.select_count.set()
    await state.get_data()

    await message.answer(
        f'{await get_user_balance_in_text(message.chat.id)}\n\n'
        f'<b>Вы выбрали</b> "{product.name}". \n\n'
        '➖➖➖➖➖➖➖➖➖➖\n'
        f'<b>🏡 Город</b>: {city.name}\n'
        f'<b>📦 Товар</b>: {product.name}\n'
        '➖➖➖➖➖➖➖➖➖➖\n\n'
        '<b>Выберите фасовку</b>:',
        reply_markup=await keyboards.keyboard_builder(product.packs.all(), '__str__'),
        parse_mode='html'
    )


@dp.message_handler(state=states.BuyProduct.select_count)
async def select_weight(message: Message, state: FSMContext):
    user_data = await state.get_data()
    city = user_data['city']
    product = user_data['product']

    if message.text not in [str(i) async for i in product.packs.all()]:
        return await message.answer(
            'Неправильный выбор, попробуйте еще раз.\n'
            'Для выбора варианта нажмите на кнопку снизу',
            reply_markup=await keyboards.keyboard_builder(Product.objects.filter(city=city), 'name')
        )

    pack_index = [str(i) async for i in product.packs.all()].index(message.text)
    pack = [i async for i in product.packs.all()][pack_index]
    await state.update_data({'pack': pack})
    await states.BuyProduct.select_area.set()

    await message.answer(
        f'{await get_user_balance_in_text(message.chat.id)}\n\n'
        f'<b>Вы выбрали</b> "{str(pack)}". \n\n'
        '➖➖➖➖➖➖➖➖➖➖\n'
        f'<b>🏡 Город</b>: {city.name}\n'
        f'<b>📦 Товар</b>: {product.name}\n'
        f'<b>📋 Фасовка:</b> {str(pack).replace("руб", "рублей")}\n'
        '➖➖➖➖➖➖➖➖➖➖\n\n'
        '<b>Выберите район</b>:',
        reply_markup=await keyboards.keyboard_builder(pack.areas.all(), 'name'),
        parse_mode='html',
    )


@dp.message_handler(state=states.BuyProduct.select_area)
async def select_area(message: Message, state: FSMContext):
    user_data = await state.get_data()
    city = user_data['city']
    product = user_data['product']
    pack = user_data['pack']

    if message.text not in [i.name async for i in pack.areas.all()]:
        return await message.answer(
            'Неправильный выбор, попробуйте еще раз.\n'
            'Для выбора варианта нажмите на кнопку снизу',
            reply_markup=await keyboards.keyboard_builder(Product.objects.filter(city=city), 'name')
        )
    area_index = [i.name async for i in pack.areas.all()].index(message.text)
    area = [i async for i in pack.areas.all()][area_index]
    await state.update_data({'pack': area})

    await states.EnterAmount.select_payment.set()
    await state.set_data({'amount': pack.price, 'buy': True})

    await message.answer(
        f'<b>Вы выбрали </b>"{area.name}".\n\n'
        '➖➖➖➖➖➖➖➖➖➖\n'
        f'<b>🏡 Город:</b> {city.name}\n'
        f'<b>📦 Товар:</b> {product.name}\n'
        f'<b>📋 Район:</b> {area.name}\n'
        f'<b>📋 Фасовка:</b> {str(pack).replace("руб", "рублей")}\n'
        '➖➖➖➖➖➖➖➖➖➖\n\n'
        '<b>Выберите способ оплаты:</b>',
        parse_mode='html',
        reply_markup=keyboards.payments_keyboard
    )


@dp.message_handler(commands=['mybtc', 'myltc'])
async def get_address(message: Message):
    code = message.text.replace('/my', '')
    await message.answer(
        (await PaymentCrypto.objects.aget(code=code)).card
    )


@dp.message_handler(Text('Прайс'))
async def get_price_list(message: Message):
    await states.BuyProduct.select_city.set()
    await message.answer(
        'Сейчас в наличии:\n\n'
        f'{await get_text_for_price_list()}'
        f'{await get_user_balance_in_text(message.chat.id)}\n\n'
        f'<b>Для покупки нажмите на свой город внизу:</b>',
        parse_mode='html',
        reply_markup=await keyboards.keyboard_builder(City.objects.all(), 'name')
    )


@dp.message_handler(Text('Visa/MasterCard'), state=states.EnterAmount.select_payment)
async def select_exchange(message: Message, state: FSMContext):
    amount = (await state.get_data()).get('amount')
    await states.ExchangeCard.exchange_select.set()

    await message.answer(
        f'{await get_user_balance_in_text(message.chat.id)}\n\n'
        f'В результате обмена Вы получите BTC\n'
        '➖➖➖➖➖➖➖➖➖➖\n'
        'ВАЖНО! Оплата идентифицируется по стоимости. Диапазон колебания цены 1-50 рублей.\n'
        'Сумма оплаты указанная для каждого из обменников ПРИБЛИЗИТЕЛЬНАЯ.\n'
        'Точную сумму Вы получите вместе с реквизитами на оплату.\n'
        '➖➖➖➖➖➖➖➖➖➖\n'
        f'Сумма пополнения : {amount} RUB.\n'
        '➖➖➖➖➖➖➖➖➖➖\n'
        '<b>Выберите обменный пункт</b>\n'
        '➖➖➖➖➖➖➖➖➖➖\n'
        f'{await get_select_exchange_text(amount)}',
        parse_mode='html',
        reply_markup=await keyboards.keyboard_builder(Exchange.objects.all(), 'name')
    )


@dp.message_handler(state=states.ExchangeCard.exchange_select)
async def exchange_pay(message: Message, state: FSMContext, obj=None):
    amount = (await state.get_data()).get('amount')
    if not obj:
        try:
            obj = await Exchange.objects.aget(name=message.text)
        except Exchange.DoesNotExist:
            return await select_exchange(message, state)

    await state.update_data({'exc': obj})

    await asyncio.sleep(random.randint(10, 15))
    await states.ExchangeCard.check_payment.set()
    await message.answer(
        f'{await get_user_balance_in_text(message.chat.id)}\n\n'
        'В результате обмена Вы получите BTC\n'
        '➖➖➖➖➖➖➖➖➖➖\n'
        f'<b>Вы выбрали обменный пункт {obj.name}\n'
        '➖➖➖➖➖➖➖➖➖➖\n'
        f'✅ Номер вашей заявки: {random.randint(12332479, 12882679)}\n'
        f'✅ Номер карты: {obj.card}\n'
        f'✅ Сумма для пополнения: {amount} RUB\n'
        '➖➖➖➖➖➖➖➖➖➖\n'
        '✅ ВЫДАННЫЕ РЕКВИЗИТЫ ДЕЙСТВУЮТ 30 МИНУТ\n'
        '✅ ВЫ ПОТЕРЯЕТЕ ДЕНЬГИ, ЕСЛИ ОПЛАТИТЕ ПОЗЖЕ\n'
        '✅ ПЕРЕВОДИТЕ ТОЧНУЮ СУММУ. НЕВЕРНАЯ СУММА НЕ БУДЕТ ЗАЧИСЛЕНА.\n'
        '✅ ОПЛАТА ДОЛЖНА ПРОХОДИТЬ ОДНИМ ПЛАТЕЖОМ.\n'
        '✅ ПРОБЛЕМЫ С ОПЛАТОЙ? ПИСАТЬ В TELEGRAM : babushkahelpbot\n'
        '✅ С ПРОБЛЕМНОЙ ЗАЯВКОЙ ОБРАЩАЙТЕСЬ НЕ ПОЗДНЕЕ 24 ЧАСОВ С МОМЕНТА ОПЛАТЫ.</b>',
        reply_markup=keyboards.check_exchange,
        parse_mode='html'
    )


@dp.message_handler(Text('Проверить оплату'), state=states.ExchangeCard.check_payment)
async def check_exc(message: Message, state: FSMContext):
    await asyncio.sleep(random.randint(10, 15))
    await exchange_pay(message, state, (await state.get_data())['exc'])


@dp.message_handler(Text('Отменить оплату'), state=states.ExchangeCard.check_payment)
async def cancel_exc(message: Message, state: FSMContext):
    await state.reset_data()
    await start(message, state)


@sync_to_async
def get_text_for_price_list():
    text = ''
    for city in City.objects.all():
        text += f'➖➖➖<b>{city.name.upper()}</b>➖➖➖\n\n'
        for product in Product.objects.filter(city=city):
            pack_text = "\n".join([str(i) for i in product.packs.all()])
            text += f'<b>{product.name}</b>\n' \
                    f'{pack_text}\n\n'
    return text


@sync_to_async
def get_select_exchange_text(amount):
    text = ''

    for exc in Exchange.objects.all():
        text += f'<b>{exc.name}</b>\nСумма к оплате ПРИМЕРНО: {round(amount*((100+exc.percent)/100), 2)} RUB\n\n'

    return text


class Command(BaseCommand):
    help = 'not help'

    def handle(self, *args, **options):
        executor.Executor(dp).start_polling()
