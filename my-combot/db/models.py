from tortoise.models import Model
import tortoise.fields as fields
class Chat(Model):
    chat_id = fields.IntField(pk=True)
    name = fields.TextField()
    added_to_group = fields.DatetimeField(auto_now_add=True)
    #TODO: log messages
