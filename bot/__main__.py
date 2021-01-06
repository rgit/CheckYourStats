from aiogram import executor
from bot.misc import dp
from bot.utils.predict import Model
import bot.handlers

model = Model()

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
