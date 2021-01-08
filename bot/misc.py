import logging
from aiogram import Bot, Dispatcher, types, filters
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from bot.config import Config


class HasPermissions(filters.BoundFilter):
    key = "has_owner_perms"

    def __init__(self, has_owner_perms):
        self.value = has_owner_perms # what should we get

    async def check(self, message: types.Message):
        user = await bot.get_chat_member(message.chat.id, message.from_user.id)
        is_admin = user["status"] == ("administrator" or "creator")
        return self.value == is_admin


bot = Bot(Config.API_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.filters_factory.bind(HasPermissions)

logging.basicConfig(level=logging.INFO)

