import asyncio
import json
import random
import subprocess
from datetime import UTC, datetime, timedelta

from fastapi import WebSocket

from backend.app.code_gen import generate_aigame_code
from backend.app.config import GEMINI_API_KEY, GEMINI_MODEL_NAME, system_instructions
from backend.app.db import db
from backend.app.models import AIGame

aigames = db.aigames


class AIGameConnectionManager:
    """
    Manages active WebSocket connections for AI games.
    """

    def __init__(self) -> None:
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, game_id: str) -> None:
        """
        Establishes a new WebSocket connection for a given game ID.
        """
        await websocket.accept()
        self.active_connections[game_id] = websocket

    def disconnect(self, game_id: str) -> None:
        """
        Closes the WebSocket connection for a given game ID.
        """
        self.active_connections.pop(game_id, None)

    async def send_state(self, game_id: str, game_data: dict) -> None:
        """
        Sends the current game state to the connected WebSocket client for a given game ID.
        Converts 'expires_at' to ISO format if present.
        """
        if game_id in self.active_connections:
            if game_data.get("expires_at"):
                expires_at = game_data["expires_at"]
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=UTC)
                else:
                    expires_at = expires_at.astimezone(UTC)
                game_data["expires_at"] = expires_at.isoformat()
            await self.active_connections[game_id].send_json(game_data)


manager = AIGameConnectionManager()


async def create_aigame(game: AIGame) -> str:
    """
    Creates a new AI game entry in the database.
    Initializes game state, shuffles the deck, and generates a unique game ID.
    """
    words = list(game.deck)
    random.shuffle(words)

    if (game.settings.word_amount is not None) and (
        1 < game.settings.word_amount < len(words)
    ):
        words = words[: game.settings.word_amount]

    code = await generate_aigame_code()

    new_game = {
        "_id": code,
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


async def start_aigame_service(game_id: str):
    """
    Starts an AI game by setting its state to 'in_progress' and processing the first word.
    """
    await aigames.update_one({"_id": game_id}, {"$set": {"game_state": "in_progress"}})
    await process_new_word(game_id)


async def process_new_word(game_id: str):
    """
    Processes the next word in the game.
    If no remaining words, sets game state to 'finished'.
    Generates a new clue and updates the game state.
    """
    game = await aigames.find_one({"_id": game_id})
    if not game or not game.get("remaining_words"):
        await aigames.update_one({"_id": game_id}, {"$set": {"game_state": "finished"}})
        finished_game = await aigames.find_one({"_id": game_id})
        if finished_game:
            await manager.send_state(game_id, finished_game)
        return

    new_word = game["remaining_words"].pop(0)
    expires_at = datetime.now(UTC) + timedelta(
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

    context_words = random.sample(game["deck"], k=min(len(game["deck"]), 3))
    first_clue = await generate_clue(new_word, context_words=context_words)
    await aigames.update_one({"_id": game_id}, {"$push": {"clues": first_clue}})

    updated_game = await aigames.find_one({"_id": game_id})
    if updated_game:
        await manager.send_state(game_id, updated_game)


async def generate_clue(
    word: str,
    previous_clues: list[str] | None = None,
    context_words: list[str] | None = None,
) -> str:
    """
    Generates a new clue for a given word using the Gemini API.
    Considers previous clues and context words to generate a unique and relevant clue.
    """
    if previous_clues is None:
        previous_clues = []
    if context_words is None:
        context_words = []

    prompt = f"WORD: {word}\n"
    prompt += f"OTHER WORDS IN DECK: {', '.join(context_words)}\n"
    if previous_clues:
        prompt += "PREVIOUS CLUES:" + ", ".join(previous_clues)

    data = {
        "generationConfig": {
            "stopSequences": [".", "?", "!", "\n"],
            "temperature": 0.8,
            "maxOutputTokens": 50,
            "topP": 0.95,
        },
        "system_instruction": {"parts": [{"text": f"{system_instructions}"}]},
        "contents": [{"parts": [{"text": f"{prompt}"}]}],
    }

    curl_command = [
        "curl",
        f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL_NAME}:generateContent",
        "-X",
        "POST",
        "-H",
        "Content-Type: application/json",
        "-H",
        f"x-goog-api-key: {GEMINI_API_KEY}",
        "-d",
        json.dumps(data),
    ]

    try:
        result = subprocess.run(
            curl_command, capture_output=True, text=True, check=True
        )

        response_json = json.loads(result.stdout)
        generated_text = response_json['candidates'][0]['content']['parts'][0]['text']

        return generated_text.strip() or ""

    except subprocess.CalledProcessError as e:
        error_message = "Error executing curl command:\n"
        error_message += f"Exit Code: {e.returncode}\n"

        return error_message


async def handle_guess(game_id: str, guess: str):
    """
    Handles a player's guess for the current word.
    If correct, increments score and processes a new word. Otherwise, generates a new clue.
    """
    game = await aigames.find_one({"_id": game_id})
    if not game or game.get("game_state") != "in_progress":
        return

    if guess.lower() == game.get("current_word", "").lower():
        await aigames.update_one({"_id": game_id}, {"$inc": {"score": 1}})
        await process_new_word(game_id)
    else:
        context_words = random.sample(game["deck"], k=min(len(game["deck"]), 3))
        new_clue = await generate_clue(
            game["current_word"], game.get("clues", []), context_words=context_words
        )
        await aigames.update_one({"_id": game_id}, {"$push": {"clues": new_clue}})
        updated_game = await aigames.find_one({"_id": game_id})
        if updated_game:
            await manager.send_state(game_id, updated_game)


async def skip_word(game_id: str):
    """
    Skips the current word and processes a new one.
    """
    await process_new_word(game_id)


async def check_timer(game_id: str):
    """
    Periodically checks if the time for guessing the current word has expired.
    If expired, processes a new word.
    """
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
            expires_at = expires_at.replace(tzinfo=UTC)

        now = datetime.now(UTC)
        if now >= expires_at:
            await process_new_word(game_id)

        await asyncio.sleep(1)
