from aiogram.utils.exceptions import MessageToDeleteNotFound, MessageCantBeDeleted, NotEnoughRightsToRestrict, BadRequest
from aiogram.dispatcher.handler import SkipHandler, CancelHandler
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InputFile
import matplotlib.style as mplstyle
from bot.modules.database import *
import matplotlib.pyplot as plt
from bot.config import Config
from io import BytesIO
import dateparser
import logging
import asyncio
import seaborn
import pandas
import time
import pytz
import gc


mplstyle.use("fast")

# Configuring logging.
logging.basicConfig(level=logging.INFO)

# Initializing bot and dispatcher.
bot = Bot(token=Config.API_TOKEN)
dp = Dispatcher(bot)


def select_with_utc_aware(chat_id: str):
    for row in select(p for p in Messages if p.chat_id == str(chat_id))[:]:
        data = row.to_dict()
        data["datetime"] = data["date"].replace(tzinfo=pytz.UTC)
        yield data


async def remove_message(message: types.Message, delay: int):
    if Config.REMOVE_COMMAND_AFTER_USAGE:
        await asyncio.sleep(delay)
        try:
            await message.delete()
        except (MessageToDeleteNotFound, MessageCantBeDeleted):
            pass


@dp.message_handler(commands="start")
@db_session
async def start_handler(message: types.Message):
    msg = await message.reply(f"Этот бот обслуживает {len([chat for chat in Chats.select()])} чата(-ов).")
    await remove_message(msg, 15)


@dp.message_handler(commands="stats")
@db_session
async def stats_handler(message: types.Message):
    await bot.delete_message(message.chat.id, message.message_id)
    response = db.select(
        f"""SELECT name, user_id, count(*) FROM Messages WHERE chat_id = '{message.chat.id}'
         GROUP BY user_id ORDER BY count(*) DESC;""")
    answer, count = f"*Статистика сообщений:*", 0
    for _message in response:
        answer += f"\n• `{_message[0]}` – {_message[2]}"
        count += _message[2]
    answer += f"\n*Общее количество сообщений: {count}.*"
    msg = await message.answer(answer, parse_mode="Markdown", disable_notification=True)
    await remove_message(msg, 15)


@dp.message_handler(commands="profile")
@db_session
async def profile_handler(message: types.Message):
    await bot.delete_message(message.chat.id, message.message_id)
    if message.reply_to_message is None:
        try:
            if message.text.split()[1]:
                user_id = [user.user_id for user in Users.select() if f"@{user.username}" ==
                           str(message.text.split()[1]) and user.chat_id == str(message.chat.id)]
                if not user_id:
                    msg = await message.answer("Пользователь не найден.")
                    await remove_message(msg, 15)
                    raise CancelHandler
                else:
                    user_id = user_id[0]
        except IndexError:
            user_id = message.from_user.id
    else:
        user_id = message.reply_to_message["from"]["id"]
    response = db.select(
        f"""SELECT username, count(*) FROM Messages WHERE (chat_id = '{message.chat.id}'
         and user_id = '{user_id}')""")[0]
    user = (await bot.get_chat_member(message.chat.id, user_id))
    msg = await message.answer(f"*Профиль пользователя* `{user['user']['first_name']}`:\n"
                               f"Айди – `{user['user']['id']}`\nСтатус – `{user['status']}`\n"
                               f"Количество сообщений – {response[1]}.",
                               parse_mode="Markdown")
    await remove_message(msg, 15)


@dp.message_handler(content_types=types.ContentTypes.ANY)
@db_session
async def message_handler(message: types.Message):
    if not [chat for chat in Chats.select() if chat.chat_id == str(message.chat.id)]:
        Chats(chat_id=str(message.chat.id), date=message.date)
        commit()
    if not [user for user in Users.select() if user.user_id == str(message.from_user.id)]:
        Users(user_id=str(message.from_user.id), chat_id=str(message.chat.id), name=message.from_user.full_name,
              username=message.from_user.username if message.from_user.username else "None", score=3, date=message.date)
        commit()

    Messages(user_id=str(message.from_user.id), chat_id=str(message.chat.id), name=message.from_user.full_name,
             username=message.from_user.username if message.from_user.username else "None", date=message.date)
    commit()

    if Config.ANTISPAM:
        user = [user for user in Users.select() if user.user_id == str(message.from_user.id)]
        if user[0].score <= 0:
            user[0].set(**{"score": 3})
            commit()
            try:
                await bot.restrict_chat_member(message.chat.id, message.from_user.id, until_date=time.time() + (60 * 5))
                msg = await message.answer(f"[{message.from_user.full_name}](tg://user?id={message.from_user.id}) был "
                                           "заблокирован на 5 минут из-за попытки спама.", parse_mode="Markdown")
                await remove_message(msg, 15)
            except (NotEnoughRightsToRestrict, BadRequest) as e:
                print(e)
                await message.answer("Прекрати спамить, долбаеб.")
            raise CancelHandler
        if message.text in ["/plot", "/cumplot"]:
            user[0].set(**{"score": user[0].score - 1})
            commit()
            raise SkipHandler
        else:
            if user[0].score < 3:
                user[0].set(**{"score": user[0].score + 1})
                commit()
    else:
        raise SkipHandler


@dp.message_handler(commands=["plot", "cumplot"])
@db_session
async def plot_handler(message: types.Message):
    figure = plt.figure()
    try:
        rule = message.text.split()[1]
    except IndexError:
        rule = "120S"
    try:
        from_ = dateparser.parse(message.text.split(maxsplit=2)[2], settings={"TIMEZONE": "UTC"})
    except IndexError:
        from_ = Messages.select().first().date.replace(tzinfo=pytz.UTC)

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

    figure.autofmt_xdate()
    plotting_t2 = time.process_time()

    tmp = BytesIO()
    image_t1 = time.process_time()
    figure.savefig(tmp)
    figure.clear()
    plt.close(figure)
    df = pandas.DataFrame()
    tmp.seek(0)
    msg = await message.reply_photo(InputFile(tmp), parse_mode="Markdown",
                                    caption=f"Plotting T=`{round((plotting_t2 - plotting_t1) * 1000, 2)}ms`\n"
                                            f"Image T=`{round((time.process_time() - image_t1) * 1000, 2)}ms`",)
    
    gc.collect()
    await bot.delete_message(message.chat.id, message.message_id)
    await remove_message(msg, 15)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
