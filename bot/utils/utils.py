import pytz
import asyncio
from bot.database import *
from aiogram.utils.exceptions import MessageToDeleteNotFound, MessageCantBeDeleted, BadRequest, \
    NotEnoughRightsToRestrict
from aiogram import types
from bot.misc import bot


def select_with_utc_aware(chat_id: str):
    for row in select(p for p in Messages if p.chat_id == str(chat_id))[:]:
        data = row.to_dict()
        data["datetime"] = data["date"].replace(tzinfo=pytz.UTC)
        yield data


async def remove_bot_message(message: types.Message, delay: int):
    if Config.REMOVE_COMMAND_AFTER_USAGE:
        await asyncio.sleep(delay)
        try:
            await message.delete()
        except (MessageToDeleteNotFound, MessageCantBeDeleted, BadRequest):
            pass


async def remove_user_message(message: types.Message):
    if Config.REMOVE_COMMAND_AFTER_USAGE:
        try:
            await bot.delete_message(message.chat.id, message.message_id)
        except (MessageToDeleteNotFound, MessageCantBeDeleted, BadRequest):
            pass

