from os import getenv
from motor.motor_asyncio import AsyncIOMotorClient

# Determine the MongoDB connection URI.
# It first tries to get it from the MONGO_URI environment variable,
# then from MONGO_URL, and defaults to "mongodb://localhost:27017/" if neither is set.
MONGO_URI = getenv("MONGO_URI") or getenv("MONGO_URL", "mongodb://localhost:27017/")

# Initialize an asynchronous MongoDB client using the determined URI.
client: AsyncIOMotorClient = AsyncIOMotorClient(MONGO_URI)

# Access the 'db' database from the client.
# This object will be used for all database operations.
db = client.db
