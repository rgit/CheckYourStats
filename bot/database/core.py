from datetime import datetime
from pony.orm import *
from bot.config import Config


db = Database()
db.bind(provider="postgres", user=Config.POSTGRES_USER, password=Config.POSTGRES_PASSWORD,
        host=Config.POSTGRES_HOST, port=Config.POSTGRES_PORT, database=Config.POSTGRES_DB)


class Chats(db.Entity):
    id = PrimaryKey(int, auto=True)
    chat_id = Required(str)
    date = Required(datetime)


class Users(db.Entity):
    id = PrimaryKey(int, auto=True)
    user_id = Required(str)
    chat_id = Required(str)
    username = Required(str)
    name = Required(str)
    score = Required(int)
    date = Required(datetime)


class Messages(db.Entity):
    id = PrimaryKey(int, auto=True)
    user_id = Required(str)
    chat_id = Required(str)
    username = Required(str)
    name = Required(str)
    date = Required(datetime)


db.generate_mapping(create_tables=True)
