import asyncio
from datetime import datetime, timedelta, timezone
import random
from typing import Dict
from fastapi import WebSocket
from google import genai
from google.genai.types import GenerateContentConfig

from backend.app.db import db
from backend.app.models import AIGame
from backend.app.config import GEMINI_API_KEY, GEMINI_MODEL_NAME, system_instructions
from backend.app.code_gen import generate_aigame_code

client = genai.Client(api_key=GEMINI_API_KEY)

aigames = db.aigames


class AIGameConnectionManager:
    def __init__(self) -> None:
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, game_id: str) -> None:
        await websocket.accept()
        self.active_connections[game_id] = websocket

    def disconnect(self, game_id: str) -> None:
        self.active_connections.pop(game_id, None)

    async def send_state(self, game_id: str, game_data: dict) -> None:
        if game_id in self.active_connections:
            if "expires_at" in game_data and game_data["expires_at"]:
                expires_at = game_data["expires_at"]
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
                else:
                    expires_at = expires_at.astimezone(timezone.utc)
                game_data["expires_at"] = expires_at.isoformat()
            await self.active_connections[game_id].send_json(game_data)


manager = AIGameConnectionManager()


async def create_aigame(game: AIGame) -> str:
    words = list(game.deck)
    random.shuffle(words)

    if (game.settings.word_amount is not None) and (
        1 < game.settings.word_amount < len(words)
    ):
        words = words[: game.settings.word_amount]

    code = await generate_aigame_code()

    new_game = {
        "_id": code,
        "player_id": game.player_id,
        "deck": words,
        "game_state": "pending",
        "settings": game.settings.model_dump(),
        "remaining_words": words,
        "current_word": None,
        "clues": [],
        "score": 0,
        "expires_at": None,
    }
    await aigames.insert_one(new_game)
    return code


async def process_new_word(game_id: str):
    game = await aigames.find_one({"_id": game_id})
    if not game or not game.get("remaining_words"):
        await aigames.update_one({"_id": game_id}, {"$set": {"game_state": "finished"}})
        finished_game = await aigames.find_one({"_id": game_id})
        if finished_game:
            await manager.send_state(game_id, finished_game)
        return

    new_word = game["remaining_words"].pop(0)
    expires_at = datetime.now(timezone.utc) + timedelta(
        seconds=game["settings"]["time_for_guessing"]
    )

    await aigames.update_one(
        {"_id": game_id},
        {
            "$set": {
                "remaining_words": game["remaining_words"],
                "current_word": new_word,
                "expires_at": expires_at,
                "clues": [],
            }
        },
    )

    first_clue = await generate_clue(new_word)
    await aigames.update_one({"_id": game_id}, {"$push": {"clues": first_clue}})

    updated_game = await aigames.find_one({"_id": game_id})
    if updated_game:
        await manager.send_state(game_id, updated_game)


async def generate_clue(word: str, previous_clues: list[str] | None = None) -> str:
    if previous_clues is None:
        previous_clues = []
    prompt = f"Explain the word '{word}' in a single sentence."
    if previous_clues:
        prompt += " Here are the previous clues, don't repeat them: " + ", ".join(
            previous_clues
        )

    response = client.models.generate_content(
        model=GEMINI_MODEL_NAME,
        contents=prompt,
        config=GenerateContentConfig(
            system_instruction=system_instructions,
            temperature=0.8,
            max_output_tokens=50,
            top_p=1.0,
        ),
    )
    return response.text or ""


async def handle_guess(game_id: str, guess: str):
    game = await aigames.find_one({"_id": game_id})
    if not game or game.get("game_state") != "in_progress":
        return

    if guess.lower() == game.get("current_word", "").lower():
        await aigames.update_one({"_id": game_id}, {"$inc": {"score": 1}})
        await process_new_word(game_id)
    else:
        new_clue = await generate_clue(game["current_word"], game.get("clues", []))
        await aigames.update_one({"_id": game_id}, {"$push": {"clues": new_clue}})
        updated_game = await aigames.find_one({"_id": game_id})
        if updated_game:
            await manager.send_state(game_id, updated_game)


async def skip_word(game_id: str):
    await process_new_word(game_id)


async def check_timer(game_id: str):
    while True:
        game = await aigames.find_one({"_id": game_id})
        if (
            not game
            or game.get("game_state") != "in_progress"
            or not game.get("expires_at")
        ):
            break

        expires_at = game["expires_at"]
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        if now >= expires_at:
            await process_new_word(game_id)

        await asyncio.sleep(1)
