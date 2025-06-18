from random import choice
from string import ascii_uppercase, digits
from backend.app.db import db

async def generate_code():
    while True:
        code = "".join(choice(ascii_uppercase + digits) for _ in range(6))
        if not await db.games.find_one({"_id": code}):
            return code