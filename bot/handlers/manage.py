from aiogram.dispatcher.handler import CancelHandler, SkipHandler
from bot.utils import *
from bot.misc import dp, types
from bot.database import *
from aiogram.types import InputFile


@dp.message_handler(commands="kick")
@db_session
async def kick_handler(message: types.Message):
    user_id = None
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
            await message.answer("Введите айди пользователя или отправьте эту команду в ответ на сообщение.")
    else:
        user_id = message.reply_to_message["from"]["id"]
    user = (await bot.get_chat_member(message.chat.id, user_id))
    try:
        await bot.kick_chat_member(message.chat.id, user_id)
        await bot.unban_chat_member(message.chat.id, user_id)
    except BadRequest:
        pass
    msg = await message.answer(f"[{user['user']['first_name']}](tg://user?id={user_id}) был кикнут.")
    await remove_bot_message(msg, 15)
