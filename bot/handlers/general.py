from aiogram.dispatcher.handler import CancelHandler, SkipHandler
from bot.utils import *
from bot.misc import dp, types
from bot.__main__ import model
from bot.database import *
import time


@dp.message_handler(commands="start")
@db_session
async def start_handler(message: types.Message):
    await remove_user_message(message)
    msg = await message.answer(f"Этот бот обслуживает {len([chat for chat in Chats.select()])} чата(-ов).")
    await remove_bot_message(msg, 15)


@dp.message_handler(commands="stats")
@db_session
async def stats_handler(message: types.Message):
    await remove_user_message(message)
    response = db.select(
        f"""SELECT name, user_id, count(*) FROM Messages WHERE chat_id = '{message.chat.id}'
         GROUP BY name, user_id ORDER BY count(*) DESC;""")
    answer, count = f"*Статистика сообщений:*", 0
    for _message in response[:10]:
        answer += f"\n• `{_message[0]}` – {_message[2]}"
        count += _message[2]
    dataset = model.get_info()
    answer += f"\n*Общее количество сообщений:* `{count}`\n*Количество записей в датасете:* `{dataset[0]}` / " \
              f"`{dataset[1]}` *спама*\n*Точность модели:* `{dataset[2]}`"
    msg = await message.answer(answer, disable_notification=True)
    await remove_bot_message(msg, 15)


@dp.message_handler(commands="profile")
@db_session
async def profile_handler(message: types.Message):
    await remove_user_message(message)
    if message.reply_to_message is None:
        try:
            if message.text.split()[1]:
                user_id = [user.user_id for user in Users.select() if f"@{user.username}" ==
                           str(message.text.split()[1]) and user.chat_id == str(message.chat.id)]
                if not user_id:
                    msg = await message.answer("Пользователь не найден.")
                    await remove_bot_message(msg, 15)
                    raise CancelHandler
                else:
                    user_id = user_id[0]
        except IndexError:
            user_id = message.from_user.id
    else:
        user_id = message.reply_to_message["from"]["id"]
    response = db.select(
        f"""SELECT username, count(*) FROM Messages WHERE (chat_id = '{message.chat.id}'
         and user_id = '{user_id}') GROUP BY username""")[0]
    user = (await bot.get_chat_member(message.chat.id, user_id))
    dataset = model.get_info(user_id)
    msg = await message.answer(f"*Профиль пользователя* `{user['user']['first_name']}`:\n"
                               f"Айди – `{user['user']['id']}`\nСтатус – `{user['status']}`\n"
                               f"Количество сообщений – `{response[1]}`\nКоличество записей в датасете – `{dataset[0]}`"
                               f"\nКоличество спама – `{dataset[1]}`")
    await remove_bot_message(msg, 15)


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
    if message.text is not None:
        prediction = model.predict(message.text)
        model.add_to_dataset(message.from_user.id, message.chat.id, message.text, prediction)
        if Config.ANTISPAM and await is_admin(message) is False:
            user = [user for user in Users.select() if user.user_id == str(message.from_user.id)]
            if prediction:
                user[0].set(**{"score": user[0].score - 1})
                commit()
                if user[0].score - 1 > 0:
                    await remove_user_message(message)
                    msg = await message.answer(f"[{message.from_user.full_name}](tg://user?id={message.from_user.id}), "
                                               f"прекратите спамить. У вас осталось {user[0].score - 1} попытки(-а).")
                    await remove_bot_message(msg, 10)
                elif user[0].score - 1 == 0:
                    await remove_user_message(message)
                    try:
                        await bot.restrict_chat_member(message.chat.id, message.from_user.id,
                                                       until_date=time.time()+ (60 * 5))
                        msg = await message.answer(
                            f"[{message.from_user.full_name}](tg://user?id={message.from_user.id}) был "
                            "заблокирован на 5 минут из-за попытки спама.")
                        await remove_bot_message(msg, 15)
                    except (NotEnoughRightsToRestrict, BadRequest):
                        print(True)
                raise SkipHandler
            else:
                if user[0].score < 3:
                    user[0].set(**{"score": user[0].score + 1})
                    commit()
        else:
            raise SkipHandler
