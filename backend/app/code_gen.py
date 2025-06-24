from random import choice
from string import ascii_uppercase, digits, ascii_lowercase
import db
from InnoAlias.backend.app.routers.auth import users
from InnoAlias.backend.app.services.game_service import decks
from InnoAlias.backend.app.services.game_service import games



async def generate_game_code():
    while True:
        code = "".join(choice(ascii_uppercase + digits) for _ in range(6))
        if not await games.find_one({"_id": code}):
            return code


async def generate_deck_id():
    while True:
        deck_id = "".join(choice(digits) for _ in range(10))
        if not await decks.find_one({"_id": deck_id}):
            return deck_id


async def generate_user_id():
    while True:
        user_id = "".join(choice(ascii_lowercase + digits) for _ in range(8))
        if not await users.find_one({"_id": user_id}):
            return user_id