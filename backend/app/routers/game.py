from asyncio import wait_for, TimeoutError, Lock
from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from pymongo import ReturnDocument
from random import shuffle
from datetime import datetime, timedelta, timezone

from ..code_gen import generate_code
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
                scores=state.get("scores", {}),
                current_correct=state.get("current_correct", 0),
                right_answers_to_advance=state.get("right_answers_to_advance", 1),
            ).model_dump(mode="json")

            await host_ws.send_json(host_state)

            for ws, name in self.players.get(game_id, []):
                tries_per_player = state.get("tries_per_player", 0)
                attempts = state.get("player_attempts", {}).get(name, 0)
                tries_left = None
                if tries_per_player:
                    tries_left = max(tries_per_player - attempts, 0)

                pg_state = PlayerGameState(
                    expires_at=state["expires_at"],
                    state=state["state"],
                    remaining_words_count=len(state.get("remaining_words", [])),
                    scores=state.get("scores", {}),
                    tries_left=tries_left,
                ).model_dump(mode="json")

                await ws.send_json(pg_state)


manager = ConnectionManager()


@router.post("/create")
async def create_game(game: Game):
    words = game.remaining_words
    shuffle(words)

    amount = game.words_amount if game.words_amount is not None else len(words)
    
    code = await generate_code()
    new_game = {
        "_id": code,
        "remaining_words": words[:amount],
        "current_word": None,
        "expires_at": None,
        "tries_per_player": game.tries_per_player,
        "right_answers_to_advance": game.right_answers_to_advance,
        "current_correct": 0,
        "player_attempts": {},
        "correct_players": [],
        "time_for_guessing": game.time_for_guessing,
        "state": "pending",
    }

    result = await games.insert_one(new_game)
    return {"id": str(result.inserted_id)}


async def process_new_word(game_id: str, sec: int) -> dict:
    game_before_pop = await games.find_one_and_update(
        {"_id": game_id, "remaining_words.0": {"$exists": True}},
        {"$pop": {"remaining_words": 1}},
        return_document=ReturnDocument.BEFORE,
    )

    if not game_before_pop:
        updated_game = await games.find_one_and_update(
            {"_id": game_id},
            {
                "$set": {
                    "current_word": None,
                    "expires_at": None,
                    "state": "finished",
                    "remaining_words": [],
                    "current_correct": 0,
                    "player_attempts": {},
                    "correct_players": [],
                }
            },
            return_document=ReturnDocument.AFTER,
        )

        return updated_game

    new_word = game_before_pop["remaining_words"][-1]

    updated_game = await games.find_one_and_update(
        {"_id": game_id},
        {
            "$set": {
                "current_word": new_word,
                "expires_at": datetime.now(timezone.utc) + timedelta(seconds=sec),
                "state": "in_progress",
                "current_correct": 0,
                "player_attempts": {},
                "correct_players": [],
            }
        },
        return_document=ReturnDocument.AFTER,
    )

    return updated_game


@router.websocket("/{game_id}")
async def handle_game(websocket: WebSocket, game_id: str):
    if not await games.find_one({"_id": game_id}):
        await websocket.close(code=1011, reason="Game not found")
        return

    is_connected = await manager.connect_host(websocket, game_id)
    if not is_connected:
        return

    try:
        game = await games.find_one({"_id": game_id})
        await manager.broadcast_state(game_id, game)

        while True:
            game = await games.find_one({"_id": game_id})
            if not game:
                break

            expires_at = game.get("expires_at")
            remaining_time = None

            if game.get("state") == "in_progress" and expires_at:
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
                remaining_time = (
                    expires_at - datetime.now(timezone.utc)
                ).total_seconds()
                if remaining_time <= 0:
                    new_state = await process_new_word(
                        game_id, game["time_for_guessing"]
                    )
                    await manager.broadcast_state(game_id, new_state)
                    continue

            try:
                if remaining_time is not None:
                    data = await wait_for(
                        websocket.receive_json(), timeout=remaining_time
                    )
                else:
                    data = await websocket.receive_json()

                action = data.get("action")
                if action == "start" and game.get("state") == "pending":
                    new_state = await process_new_word(
                        game_id, game["time_for_guessing"]
                    )
                    await manager.broadcast_state(game_id, new_state)
                elif action == "skip" and game.get("state") == "in_progress":
                    print(f"Getting next word for {game_id}")
                    new_state = await process_new_word(
                        game_id, game["time_for_guessing"]
                    )
                    await manager.broadcast_state(game_id, new_state)

            except TimeoutError:
                if game.get("state") == "in_progress":
                    new_state = await process_new_word(
                        game_id, game["time_for_guessing"]
                    )
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

    if not await games.find_one({"_id": game_id}):
        await websocket.close(code=1011, reason="Game not found")
        return

    await manager.connect_player(websocket, game_id, player_name)
    await games.update_one(
        {"_id": game_id, f"scores.{player_name}": {"$exists": False}},
        {"$set": {f"scores.{player_name}": 0}},
    )
    await games.update_one(
        {"_id": game_id}, {"$set": {f"player_attempts.{player_name}": 0}}
    )

    try:
        game = await games.find_one({"_id": game_id})
        await manager.broadcast_state(game_id, game)

        while True:
            data = await websocket.receive_json()
            if data["action"] != "guess":
                continue

            guess = data.get("guess", "").strip().lower()

            async with manager.locks[game_id]:
                game = await games.find_one({"_id": game_id})
                if game["state"] != "in_progress":
                    continue

                tries_per_player = game.get("tries_per_player", 0)
                attempts = game.get("player_attempts", {}).get(player_name, 0)

                if player_name in game.get("correct_players", []):
                    continue

                if tries_per_player and attempts >= tries_per_player:
                    continue

                expires_at = game.get("expires_at")
                if expires_at and expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)

                if expires_at and datetime.now(timezone.utc) > expires_at:
                    continue

                if guess == game["current_word"].lower():
                    update = {
                        "$set": {f"player_attempts.{player_name}": attempts + 1},
                    }

                    if player_name not in game.get("correct_players", []):
                        update["$inc"] = {
                            f"scores.{player_name}": 1,
                            "current_correct": 1,
                        }
                        update["$addToSet"] = {"correct_players": player_name}

                    new_state = await games.find_one_and_update(
                        {"_id": game_id},
                        update,
                        return_document=ReturnDocument.AFTER,
                    )

                    if new_state.get("current_correct", 0) >= new_state.get(
                        "right_answers_to_advance", 1
                    ):
                        new_state = await process_new_word(
                            game_id, game["time_for_guessing"]
                        )

                else:
                    await games.update_one(
                        {"_id": game_id},
                        {"$set": {f"player_attempts.{player_name}": attempts + 1}},
                    )
                    new_state = await games.find_one({"_id": game_id})

                if new_state.get("current_correct", 0) < new_state.get(
                    "right_answers_to_advance", 1
                ):
                    tries_per_player = new_state.get("tries_per_player", 0)
                    if tries_per_player:
                        attempts_map = new_state.get("player_attempts", {})
                        all_spent = all(
                            attempts_map.get(p, 0) >= tries_per_player
                            or p in new_state.get("correct_players", [])
                            for p in new_state.get("scores", {}).keys()
                        )
                        if all_spent:
                            new_state = await process_new_word(
                                game_id,
                                new_state.get("time_for_guessing", 0),
                            )

                await manager.broadcast_state(game_id, new_state)

    except WebSocketDisconnect:
        manager.disconnect(game_id, websocket)
    except Exception as e:
        print(e)
        manager.disconnect(game_id, websocket)
