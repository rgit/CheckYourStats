import matplotlib.pyplot as plt
from io import BytesIO
import dateparser
import seaborn
import pandas
import time
import gc
from bot.utils import *
from bot.misc import dp, types
from bot.database import *
from aiogram.types import InputFile


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
    tmp.seek(0)
    msg = await message.reply_photo(InputFile(tmp),
                                    caption=f"Plotting T=`{round((plotting_t2 - plotting_t1) * 1000, 2)}ms`\n"
                                    f"Image T=`{round((time.process_time() - image_t1) * 1000, 2)}ms`", )

    gc.collect()
    await remove_user_message(message)
    await remove_bot_message(msg, 15)
