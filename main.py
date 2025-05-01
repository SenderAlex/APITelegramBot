import asyncio
import logging
import config
from config import TOKEN
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import keyboards
import requests


bot = Bot(TOKEN)
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)


class FormCryptoCurrency(StatesGroup):
    amount = State()
    from_symbol = State()
    to_symbol = State()


class FormCryptoUSDT(StatesGroup):
    crypto_amount = State()


@dp.message(CommandStart())
async def command_start(message: Message):
    await message.answer(f'Привет, {message.from_user.full_name}! Я твой БОТ по конвертации твоих криптоактивов'
                         f' и криптовалют в режиме реального времени!!', reply_markup=keyboards.main)


@dp.message(F.text == 'Конвертация криптоактивов в USDT')
async def command_hello(message: Message, state: FSMContext):
    await message.answer(f'{message.from_user.first_name.capitalize()}, Вы выбрали конвертацию криптоактивов в USDT!')
    await message.answer('Введите сумму и код всех криптовалют через запятую, которую Вы хотите конвертировать.'
                         ' Например, 1.5 BTC, 25 ETH, 100 SOL')
    await state.set_state(FormCryptoUSDT.crypto_amount)


@dp.message(FormCryptoUSDT.crypto_amount)
async def command_hello(message: Message, state: FSMContext):
    await state.update_data(crypto_amount=message.text.upper())

    currency_data = await state.get_data()
    currency_list = currency_data['crypto_amount'].split(',')
    crypto_assets_in_usdt = 0
    conversion_results = []

    for currency_entry in currency_list:
        try:
            # Парсим ввод вида "0.5 BTC" или "10 ETH"
            amount_str, symbol = currency_entry.strip().split()
            amount = float(amount_str)

            # Запрос к CoinMarketCap API
            url = config.CMC_API_URL
            params = {
                'amount': amount,
                'symbol': symbol.upper(),
                'convert': 'USDT'
            }
            headers = {'X-CMC_PRO_API_KEY': config.CMC_API_KEY}

            response = requests.get(url, headers=headers, params=params)
            data = response.json()

            # Извлекаем цену конвертации
            usdt_price = data['data'][0]['quote']['USDT']['price']
            crypto_assets_in_usdt += usdt_price

            # Форматируем результат для вывода
            conversion_results.append(
                f"{amount} {symbol.upper()} = {usdt_price:.2f} USDT"
            )

        except (ValueError, KeyError, IndexError) as e:
            await message.answer(f"Ошибка в записи: {currency_entry} ({str(e)})")
            await state.clear()
            return

    # Формируем итоговое сообщение
    await message.answer("\n".join(conversion_results) + f'\n<b>Итого: {crypto_assets_in_usdt:.2f} USDT</b>',
                         parse_mode='HTML')
    await state.clear()


@dp.message(F.text == 'Конвертация криптовалют')
async def command_hello(message: Message, state: FSMContext):
    await message.answer(f'{message.from_user.first_name.capitalize()}, Вы выбрали конвертацию криптовалют!')
    await message.answer('Введите код криптовалюты, которую Вы хотите конвертировать. Например, BTC (биткоин)')
    await state.set_state(FormCryptoCurrency.from_symbol)


@dp.message(FormCryptoCurrency.from_symbol)
async def command_hello(message: Message, state: FSMContext):
    await state.update_data(from_symbol=message.text.upper())
    await message.answer('Введите код криптовалюты, в которую Вы хотите конвертировать. Например, ETH (эфир)')
    await state.set_state(FormCryptoCurrency.to_symbol)


@dp.message(FormCryptoCurrency.to_symbol)
async def command_hello(message: Message, state: FSMContext):
    await state.update_data(to_symbol=message.text.upper())
    data = await state.get_data()
    await message.answer(f"Введите сумму криптовалюты {data['from_symbol']}, которую Вы хотите конвертировать.")
    await state.set_state(FormCryptoCurrency.amount)


@dp.message(FormCryptoCurrency.amount)
async def command_hello(message: Message, state: FSMContext):
    await state.update_data(amount=float(message.text))
    full_data = await state.get_data()
    await state.set_state(FormCryptoCurrency.to_symbol)

    try:
        url = config.CMC_API_URL
        params = {
            'amount': full_data['amount'],
            'symbol': full_data['from_symbol'],
            'convert': full_data['to_symbol']
        }
        headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': config.CMC_API_KEY,
        }
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        price = data['data'][0]['quote'][full_data['to_symbol']]['price']
        await message.answer(f"<b>{full_data['amount']} {full_data['from_symbol']} ="
                             f" {price:.8f} {full_data['to_symbol']}</b>", parse_mode='HTML')
    except Exception as e:
        await message.reply(f"Ошибка: {e}")

    await state.clear()


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())