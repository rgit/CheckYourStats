from datetime import datetime
from pony.orm import *


db = Database()
db.bind(provider="sqlite", filename="stats.sqlite", create_db=True)


class Chats(db.Entity):
    id = PrimaryKey(int, auto=True)
    chat_id = Required(str)
    date = Required(datetime, sql_type="TIMESTAMP WITH TIME ZONE")


class Users(db.Entity):
    id = PrimaryKey(int, auto=True)
    user_id = Required(str)
    chat_id = Required(str)
    username = Required(str)
    name = Required(str)
    score = Required(int)
    date = Required(datetime, sql_type="TIMESTAMP WITH TIME ZONE")


class Messages(db.Entity):
    id = PrimaryKey(int, auto=True)
    user_id = Required(str)
    chat_id = Required(str)
    username = Required(str)
    name = Required(str)
    date = Required(datetime, sql_type="TIMESTAMP WITH TIME ZONE")


db.generate_mapping(create_tables=True)
