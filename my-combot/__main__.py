from aiohttp import web
import aiogram
import tortoise
from tortoise import Tortoise

from .handlers import commands,tracker
#from . import db

from .config import *

WEBHOOK_URL = f"https://{WEBHOOK_HOST}:{WEBHOOK_PORT}{WEBHOOK_URL_PATH}"


 
bot = aiogram.Bot(TOKEN)
dp = aiogram.Dispatcher(bot)


async def on_startup(self):
    dp.register_message_handler(commands.cmd_start, commands=['start'])
    dp.register_message_handler(tracker.track_msg)

    webhook = await bot.get_webhook_info()
    if webhook.url != WEBHOOK_URL:
        if not webhook.url:
            await bot.delete_webhook()
        await bot.set_webhook(WEBHOOK_URL)


async def on_shutdown(self):
    await bot.delete_webhook()
    await Tortoise.close_connections()


if __name__ == '__main__':
    app = aiogram.dispatcher.webhook.get_new_configured_app(dispatcher=dp, path=WEBHOOK_URL_PATH)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)