from os import getenv
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = getenv("MONGO_URI") or getenv("MONGO_URL", "mongodb://localhost:27017/")
client: AsyncIOMotorClient = AsyncIOMotorClient(MONGO_URI)
db = client.db
