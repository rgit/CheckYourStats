from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher import FSMContext
from bot.utils import *
from bot.misc import dp, types
from bot.__main__ import model


class Training(StatesGroup):
    training_model = State()


@dp.message_handler(commands="train", state="*")
async def train_model_start_handler(message: types.Message):
    msg = await message.answer("<b>Обучение начато.</b> Плюс ( + ) – является, минус ( - ) – не является. Используйте /stop "
                               "чтобы закончить обучение.")
    await remove_bot_message(msg, 1)
    await bot.delete_message(message.chat.id, message.message_id)
    phrase = model.get_random_row()
    msg = await message.answer(f"<b>Фраза</b> \"<code>{phrase}</code>\" <b>является спамом?</b>")

    await dp.storage.set_data(chat=message.chat.id, user=message.from_user.id, data={
        "user_id": message.from_user.id, "message": msg, "phrase": phrase, "count": 1})

    await Training.training_model.set()


@dp.message_handler(state=Training.training_model)
@db_session
async def train_model_start_handler(message: types.Message, state: FSMContext):
    data = await dp.storage.get_data(chat=message.chat.id, user=message.from_user.id, default=None)
    if message.from_user.id == data["user_id"]:
        if message.text == "+":
            msg = await data["message"].edit_text(f"<b>Фраза</b> \"<code>{data['phrase']}</code>\" <b>помечена как спам.</b>",
                                                  parse_mode="HTML")
            model.set_spam_mark(data["phrase"], True)
            await remove_bot_message(msg, 1)
            await bot.delete_message(message.chat.id, message.message_id)
        elif message.text == "-":
            msg = await data["message"].edit_text(f"<b>Фраза</b> \"<code>{data['phrase']}</code>\" <b>помечена как НЕ спам.</b>",
                                                  parse_mode="HTML")
            model.set_spam_mark(data["phrase"], False)
            await remove_bot_message(msg, 1)
            await bot.delete_message(message.chat.id, message.message_id)
        elif message.text == "/stop":
            await remove_bot_message(data["message"], 0)
            msg = await message.answer(f"<b>Обучение завершено. Проверено</b> <code>{data['count']}</code> <b>фраз(-ы). Точность модели:</b>"
                                       f" <code>{model.get_info()[2]}</code><b>.</b>")
            await bot.delete_message(message.chat.id, message.message_id)
            await remove_bot_message(msg, 10)
            await state.finish()
            raise CancelHandler

        if message.text in ["+", "-"]:
            phrase = model.get_random_row()
            msg = await message.answer(f"<b>Фраза</b> \"<code>{phrase}</code>\" <b>является спамом?</b>")

            await dp.storage.set_data(chat=message.chat.id, user=message.from_user.id, data={
                "user_id": message.from_user.id, "message": msg, "phrase": phrase, "count": data["count"] + 1})


@dp.message_handler(commands="addspam", has_owner_perms=True)
async def add_spam_handler(message: types.Message):
    await remove_user_message(message)
    if message.reply_to_message is not None:
        if message.reply_to_message["text"] is not None:
            model.set_spam_mark(message.reply_to_message["text"], True)
            msg = await message.reply_to_message.reply("Данное сообщение помечено как спам.")
        else:
            msg = await message.answer("Сообщение должно содержать только текст.")
    else:
        msg = await message.answer("Оправьте команду в ответ на сообщение.")
    await remove_bot_message(msg, 10)


@dp.message_handler(commands="delspam", has_owner_perms=True)
async def delete_spam_handler(message: types.Message):
    await remove_user_message(message)
    if message.reply_to_message is not None:
        if message.reply_to_message["text"] is not None:
            _message = message.reply_to_message
            model.set_spam_mark(_message["text"], False)
            msg = await _message.reply("Данное сообщение помечено как НЕ спам.")
        else:
            msg = await message.answer("Сообщение должно содержать только текст.")
    else:
        msg = await message.answer("Оправьте команду в ответ на сообщение.")
    await remove_bot_message(msg, 10)

