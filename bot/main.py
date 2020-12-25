import logging

import dateparser
from datetime import datetime
import time
from tempfile import TemporaryFile

import pandas
import pytz
import seaborn
from aiogram import Bot, Dispatcher, executor, types

import dotenv
from aiogram.types import InputFile, ChatMember
from pony.orm import db_session, select
import matplotlib.pyplot as plt

from bot.db.db import ChatMessage

env = dotenv.dotenv_values()


# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=env["API_TOKEN"])
dp = Dispatcher(bot)


@dp.message_handler(commands=["start", "help"])
async def start(message: types.Message):
    await message.reply(f"""
Этот бот обслуживает чат @{env['CHAT_NAME']} 
""")


def select_with_utc_aware(chat_id):
    for row in select(p for p in ChatMessage if p.chat_id == str(chat_id))[:]:
        data = row.to_dict()
        data["datetime"] = data["datetime"].replace(tzinfo=pytz.UTC)
        yield data


@dp.message_handler(commands=["plot", "cumplot"])
async def plot(message: types.Message):
    if message.chat.id != int(env["CHAT_ID"]):
        return
    if message.from_user.id not in [a.user.id for a in (await message.chat.get_administrators())]:
        await message.reply("Только администраторы могут рисовать графики")
        return
    fig = plt.figure()

    try:
        rule = message.text.split()[1]
    except IndexError:
        rule = "120S"

    try:
        from_ = dateparser.parse(message.text.split(maxsplit=2)[2], settings={"TIMEZONE": "UTC"})
        print(from_)
    except IndexError:
        with db_session:
            from_ = ChatMessage.select().first().datetime.replace(tzinfo=pytz.UTC)

    with db_session:
        plotting_t1 = time.process_time()
        df = pandas.DataFrame(select_with_utc_aware(message.chat.id))

        df = df.rename(columns={"datetime": "Время", "amount": "Количество сообщений"})

        df = df.set_index("Время")
        df["Количество сообщений"] = 1
        df = df.resample(rule).sum()

        if message.text.startswith("/cumplot"):
            df["Количество сообщений"] = df["Количество сообщений"].cumsum()

        df = df.loc[from_:]

        seaborn.lineplot(x="Время", y="Количество сообщений", data=df)

        fig.autofmt_xdate()
        plotting_t2 = time.process_time()

        with TemporaryFile() as tmp:
            image_t1 = time.process_time()
            fig.savefig(tmp, dpi=700)
            tmp.seek(0)
            await message.reply_photo(InputFile(tmp), caption=f"""plotting T={round((plotting_t2 - plotting_t1) * 1000, 2)}ms
image T={round((time.process_time() - image_t1) * 1000, 2)}ms
Все даты в UTC""")


@dp.message_handler()
async def message_logger(message: types.Message):
    # old style:
    # await bot.send_message(message.chat.id, message.text)
    if message.chat.id != int(env["CHAT_ID"]):
        return
    with db_session:
        ChatMessage(
            id=str(message.message_id),
            chat_id=str(message.chat.id),
            user_id=str(message.from_user.id),
            datetime=datetime.utcnow().replace(tzinfo=pytz.UTC),
        )


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
