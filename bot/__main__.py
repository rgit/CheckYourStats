from aiogram import executor
from bot.misc import dp
from bot.utils import Model
import bot.handlers
from sys import argv

model = Model()

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=("--skip" in argv))

