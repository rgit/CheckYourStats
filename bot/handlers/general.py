from aiogram.dispatcher.handler import CancelHandler, SkipHandler
from bot.utils import *
from bot.misc import dp, types
from bot.__main__ import model
from bot.database import *
import random
import time


@dp.message_handler(content_types=types.ContentTypes.NEW_CHAT_MEMBERS)
async def new_member_handler(message: types.Message):
    if message.new_chat_members[0].is_bot and Config.BLOCK_BOTS:
        if message.new_chat_members[0].id != bot.id:
            await bot.kick_chat_member(message.chat.id, message.new_chat_members[0].id)
    elif not message.new_chat_members[0].is_bot:
        await bot.restrict_chat_member(message.chat.id, message.from_user.id, until_date=time.time() + (60 * 10))
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        number_1, act, number_2 = random.randint(1, 50), random.choice(["+", "-"]), random.randint(1, 50)
        answer = eval(f"{number_1} {act} {number_2}")
        rows = ((f"{answer}", "True"), (f"{random.randint(1, 50)}", "False"))
        rows = random.sample(rows, len(rows))
        row = (types.InlineKeyboardButton(text, callback_data=data) for text, data in rows)
        keyboard.row(*row)
        msg = await message.answer(f"[{message.from_user.full_name}](tg://user?id={message.from_user.id}), у вас есть "
                                   f"1 минута на решение примера: *{number_1} {act} {number_2}*.", reply_markup=keyboard)
        await dp.storage.set_data(chat=message.chat.id, user=message.from_user.id, data={
            "user_id": message.from_user.id, "message": msg, "submitted": False})
        await asyncio.sleep(60)
        data = await dp.storage.get_data(chat=message.chat.id, user=message.from_user.id, default=None)
        if data != {} and not data["submitted"]:
            msg.edit_text(f"[{message.from_user.full_name}](tg://user?id={message.from_user.id}), не прошел проверку "
                          "вовремя и был кикнут.", reply_markup="")
            try:
                await bot.kick_chat_member(message.chat.id, message.from_user.id)
                await bot.unban_chat_member(message.chat.id, message.from_user.id)
            except BadRequest:
                pass


@dp.callback_query_handler(text="True")
@dp.callback_query_handler(text="False")
async def new_member_callback_handler(query: types.CallbackQuery):
    data = await dp.storage.get_data(chat=query.message.chat.id, user=query.from_user.id, default=None)
    if data != {} and data["user_id"] == query.from_user.id:
        answer = query.data
        msg = None

        if answer == "True":
            msg = await data["message"].edit_text(f"[{query.from_user.full_name}](tg://user?id={query.from_user.id}), "
                                                  "прошел проверку. Добро пожаловать в RuGit чат.", reply_markup="")
            await dp.storage.set_data(chat=query.message.chat.id, user=query.from_user.id, data={
                "user_id": query.from_user.id, "message": msg, "submitted": True})
            await bot.restrict_chat_member(query.message.chat.id, query.from_user.id, until_date=time.time() + 31,
                                           can_send_messages=True)
        elif answer == "False":
            msg = await data["message"].edit_text(f"[{query.from_user.full_name}](tg://user?id={query.from_user.id}), "
                                                  "не прошел проверку и был кикнут.", reply_markup="")
            try:
                await bot.kick_chat_member(query.message.chat.id, query.from_user.id)
                await bot.unban_chat_member(query.message.chat.id, query.from_user.id)
            except BadRequest:
                pass
        await remove_bot_message(msg, 30)


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
