from asyncio import wait_for, TimeoutError, Lock
from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ReturnDocument
from random import shuffle
from datetime import datetime, timedelta, timezone

from ..db import db
from ..models import Game, GameState, PlayerGameState

router = APIRouter(prefix="", tags=["game"])

games = db.games


class ConnectionManager:
    def __init__(self):
        self.hosts: dict[str, WebSocket] = {}
        self.players: dict[str, list[tuple[WebSocket, str]]] = {}
        self.locks: dict[str, Lock] = {}

    async def connect_host(self, websocket: WebSocket, game_id: str) -> bool:
        await websocket.accept()

        if game_id in self.hosts:
            await websocket.close(
                code=1008, reason="Game already active and host is connected"
            )
            return False

        self.hosts[game_id] = websocket
        self.locks[game_id] = Lock()
        return True

    async def connect_player(
        self, websocket: WebSocket, game_id: str, player_name: str
    ) -> bool:
        await websocket.accept()
        self.players.setdefault(game_id, []).append((websocket, player_name))
        return True

    def disconnect(self, game_id: str, websocket: WebSocket = None):
        if self.hosts.get(game_id) is websocket:
            del self.hosts[game_id]
            del self.locks[game_id]

        else:
            lst = self.players.get(game_id, [])
            self.players[game_id] = [
                (ws, name) for ws, name in lst if ws is not websocket
            ]
            if not self.players[game_id]:
                del self.players[game_id]

    async def broadcast_state(self, game_id: str, state: dict):
        host_ws = self.hosts.get(game_id)
        if host_ws:
            host_state = GameState(
                current_word=state.get("current_word"),
                expires_at=state.get("expires_at"),
                state=state.get("state"),
                remaining_words_count=len(state.get("remaining_words", [])),
            ).model_dump(mode="json")

            await host_ws.send_json(host_state)

        pg_state = PlayerGameState(
            expires_at=state["expires_at"],
            state=state["state"],
            remaining_words_count=len(state.get("remaining_words", [])),
            scores=state.get("scores", {}),
        ).model_dump(mode="json")

        for ws, _ in self.players.get(game_id, []):
            await ws.send_json(pg_state)


manager = ConnectionManager()


@router.post("/create")
async def create_game(game: Game):
    words = game.remaining_words
    shuffle(words)

    new_game = {
        "remaining_words": words,
        "current_word": None,
        "expires_at": None,
        "state": "pending",
    }

    result = await games.insert_one(new_game)
    return {"id": str(result.inserted_id)}


async def process_new_word(game_id: ObjectId) -> dict:
    game_before_pop = await games.find_one_and_update(
        {"_id": game_id, "remaining_words.0": {"$exists": True}},
        {"$pop": {"remaining_words": 1}},
        return_document=ReturnDocument.BEFORE,
    )

    if not game_before_pop:
        await games.delete_one({"_id": game_id})
        print(f"Game {game_id} finished and entry deleted from database.")

        return {
            "state": "finished",
            "current_word": None,
            "expires_at": None,
            "remaining_words": [],
        }

    new_word = game_before_pop["remaining_words"][-1]

    updated_game = await games.find_one_and_update(
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

        if not await games.find_one({"_id": game_id_obj}):
            await websocket.close(code=1011, reason="Game not found")
            return
    except InvalidId:
        await websocket.close(code=1011, reason="GameID is invalid")
        return

    is_connected = await manager.connect_host(websocket, game_id)
    if not is_connected:
        return

    try:
        new_state = await process_new_word(game_id_obj)
        await manager.broadcast_state(game_id, new_state)

        while True:
            game = await games.find_one({"_id": game_id_obj})
            if not game or game.get("state") != "in_progress":
                break

            expires_at = game.get("expires_at")
            if not expires_at:
                break

            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            remaining_time = (expires_at - datetime.now(timezone.utc)).total_seconds()

            if remaining_time <= 0:
                new_state = await process_new_word(game_id_obj)
                await manager.broadcast_state(game_id, new_state)
                continue

            try:
                data = await wait_for(websocket.receive_json(), timeout=remaining_time)

                if data.get("action") == "skip":
                    print(f"Getting next word for {game_id}")
                    new_state = await process_new_word(game_id_obj)
                    await manager.broadcast_state(game_id, new_state)

            except TimeoutError:
                print("Timeout")
                new_state = await process_new_word(game_id_obj)
                await manager.broadcast_state(game_id, new_state)

        print(f"Game {game_id} finished")

    except WebSocketDisconnect:
        print(f"Disconnected from {game_id}")
    except Exception as e:
        print(e)
    finally:
        manager.disconnect(game_id)


@router.websocket("/{game_id}/player")
async def handle_player(websocket: WebSocket, game_id: str):
    player_name = websocket.query_params.get("name")
    if not player_name:
        await websocket.close(code=1008, reason="Missing player's name")
        return

    try:
        game_id_obj = ObjectId(game_id)
        if not await games.find_one({"_id": game_id_obj}):
            await websocket.close(code=1011, reason="Game not found")
            return
    except InvalidId:
        await websocket.close(code=1011, reason="GameID is invalid")
        return

    await manager.connect_player(websocket, game_id, player_name)

    try:
        game = await games.find_one({"_id": game_id_obj})
        await manager.broadcast_state(game_id, game)

        while True:
            data = await websocket.receive_json()
            if data["action"] != "guess":
                continue

            guess = data.get("guess", "").strip().lower()

            async with manager.locks[game_id]:
                game = await games.find_one({"_id": game_id_obj})
                if game["state"] != "in_progress":
                    continue

                expires_at = game.get("expires_at")
                if expires_at and expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)

                if expires_at and datetime.now(timezone.utc) > expires_at:
                    continue

                if guess == game["current_word"].lower():
                    await games.find_one_and_update(
                        {"_id": game_id_obj}, {"$inc": {f"scores.{player_name}": 1}}
                    )
                    new_state = await process_new_word(game_id_obj)
                    await manager.broadcast_state(game_id, new_state)

    except WebSocketDisconnect:
        manager.disconnect(game_id, websocket)
    except Exception as e:
        print(e)
        manager.disconnect(game_id, websocket)
