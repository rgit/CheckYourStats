from tortoise import Tortoise
from ..config import DB_URL
async def init():
    await Tortoise.init(
        db_url=DB_URL,
        modules={'models': ['db.models']} #TODO: verify if model path is correct
    )
    await Tortoise.generate_schemas(safe=True)