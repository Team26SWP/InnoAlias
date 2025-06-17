from models import Game, GameState
from asyncio import wait_for, TimeoutError
from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ReturnDocument
from random import shuffle
from datetime import datetime, timedelta, timezone

from db import db

router = APIRouter(prefix="", tags=["game"])

games = db.games

class ConnectionManager:
    def __init__(self):
        self.connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, game_id: str) -> bool:
        await websocket.accept()

        if game_id in self.connections:
            await websocket.close(
                code=1008, reason="Game already active and host is connected"
            )
            return False

        self.connections[game_id] = websocket
        print(f"Connected to {game_id}")

        return True

    def disconnect(self, game_id: str):
        if game_id in self.connections:
            del self.connections[game_id]
            print(f"Disconnected from {game_id}")

    async def send_state(self, game_id: str, state: dict):
        if game_id in self.connections:
            websocket = self.connections[game_id]

            game_state = GameState(
                current_word=state["current_word"],
                expires_at=state["expires_at"],
                state=state["state"],
                remaining_words_count=len(state.get("remaining_words", [])),
            )

            await websocket.send_json(game_state.model_dump(mode="json"))


manager = ConnectionManager()


@router.post("/create")
def create_game(game: Game):
    words = game.remaining_words
    shuffle(words)

    new_game = {
        "remaining_words": words,
        "current_word": None,
        "expires_at": None,
        "state": "pending",
    }

    result = games.insert_one(new_game)
    return {"id": str(result.inserted_id)}


async def process_new_word(game_id: ObjectId) -> dict:
    game_before_pop = games.find_one_and_update(
        {"_id": game_id, "remaining_words.0": {"$exists": True}},
        {"$pop": {"remaining_words": 1}},
        return_document=ReturnDocument.BEFORE,
    )

    if not game_before_pop:
        games.delete_one({"_id": game_id})
        print(f"Game {game_id} finished and entry deleted from database.")

        return {
            "state": "finished",
            "current_word": None,
            "expires_at": None,
            "remaining_words": [],
        }

    new_word = game_before_pop["remaining_words"][-1]

    updated_game = games.find_one_and_update(
        {"_id": game_id},
        {
            "$set": {
                "current_word": new_word,
                "expires_at": datetime.now(timezone.utc) + timedelta(seconds=60),
                "state": "in_progress",
            }
        },
        return_document=ReturnDocument.AFTER,
    )

    return updated_game


@router.websocket("/{game_id}")
async def handle_game(websocket: WebSocket, game_id: str):

    try:
        game_id_obj = ObjectId(game_id)

        if not games.find_one({"_id": game_id_obj}):
            await websocket.close(code=1011, reason="Game not found")
            return
    except InvalidId:
        await websocket.close(code=1011, reason="GameID is invalid")
        return

    is_connected = await manager.connect(websocket, game_id)
    if not is_connected:
        return

    try:
        new_state = await process_new_word(game_id_obj)
        await manager.send_state(game_id, new_state)

        while new_state and new_state.get("state") == "in_progress":
            expires_at = new_state["expires_at"]

            if not expires_at:
                break

            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            time_now = datetime.now(timezone.utc)
            remaining_time = (expires_at - time_now).total_seconds()

            if remaining_time <= 0:
                new_state = await process_new_word(game_id_obj)
                await manager.send_state(game_id, new_state)
                continue

            try:
                data = await wait_for(websocket.receive_json(), timeout=remaining_time)

                action = data["action"]

                if action == "skip":
                    print(f"Getting next word for {game_id}")
                    new_state = await process_new_word(game_id_obj)
                    await manager.send_state(game_id, new_state)

            except TimeoutError:
                print("Timeout")
                new_state = await process_new_word(game_id_obj)
                await manager.send_state(game_id, new_state)

        print(f"Game {game_id} finished")

    except WebSocketDisconnect:
        print(f"Disconnected from {game_id}")
    except Exception as e:
        print(e)
    finally:
        manager.disconnect(game_id)
