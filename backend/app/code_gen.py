"""Utility functions for generating unique identifiers used across the app."""

from random import choice
from string import ascii_uppercase, digits, ascii_lowercase

from backend.app.db import db
from backend.app.services.game_service import decks
from backend.app.services.game_service import games

users = db.users
aigames = db.aigames


async def generate_game_code():
    """Generate a unique six character alphanumeric game code."""
    while True:
        code = "".join(choice(ascii_uppercase + digits) for _ in range(6))
        if not await games.find_one({"_id": code}):
            return code


async def generate_aigame_code():
    """Generate a unique six digit code for an AI game."""
    while True:
        code = "".join(choice(digits) for _ in range(6))
        if not await aigames.find_one({"_id": code}):
            return code


async def generate_deck_id():
    """Generate a unique ten digit deck identifier."""
    while True:
        deck_id = "".join(choice(digits) for _ in range(10))
        if not await decks.find_one({"_id": deck_id}):
            return deck_id


async def generate_user_id():
    """Generate a unique eight character alphanumeric user identifier."""
    while True:
        user_id = "".join(choice(ascii_lowercase + digits) for _ in range(8))
        if not await users.find_one({"_id": user_id}):
            return user_id
