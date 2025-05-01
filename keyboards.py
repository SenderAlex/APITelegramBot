from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Конвертация криптоактивов в USDT")],
    [KeyboardButton(text="Конвертация криптовалют")]
], resize_keyboard=True)

