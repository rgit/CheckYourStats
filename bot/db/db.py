from datetime import datetime
from pony.orm import *


db = Database()
db.bind(provider="sqlite", filename="database.sqlite", create_db=True)


class ChatMessage(db.Entity):
    id = PrimaryKey(str)
    datetime = Required(datetime, sql_type='TIMESTAMP WITH TIME ZONE')
    chat_id = Required(str)
    user_id = Required(str)


db.generate_mapping(create_tables=True)
