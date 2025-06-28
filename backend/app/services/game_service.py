from asyncio import Lock
from datetime import datetime, timedelta, timezone
from random import choice
from typing import Optional

from fastapi import WebSocket
from pymongo import ReturnDocument

from backend.app.db import db
from backend.app.models import GameState, PlayerGameState

games = db.games
decks = db.decks


def required_to_advance(state: dict) -> int:
    names = set(state.get("scores", {}).keys())
    names.discard(state.get("current_master"))
    players_count = len(names)
    return min(state.get("right_answers_to_advance", 1), players_count)


class ConnectionManager:
    def __init__(self) -> None:
        self.hosts: dict[str, WebSocket] = {}
        self.host_names: dict[str, str] = {}
        self.players: dict[str, list[tuple[WebSocket, str]]] = {}
        self.locks: dict[str, Lock] = {}

    async def connect_host(
        self, websocket: WebSocket, game_id: str, name: Optional[str]
    ) -> bool:
        await websocket.accept()
        if game_id in self.hosts:
            await websocket.close(
                code=1008, reason="Game already active and host is connected"
            )
            return False

        self.hosts[game_id] = websocket
        if name:
            self.host_names[game_id] = name
        self.locks[game_id] = Lock()
        return True

    async def connect_player(
        self, websocket: WebSocket, game_id: str, player_name: str
    ) -> bool:
        await websocket.accept()
        self.players.setdefault(game_id, []).append((websocket, player_name))
        return True

    def disconnect(self, game_id: str, websocket: Optional[WebSocket] = None) -> None:
        if self.hosts.get(game_id) is websocket:
            del self.hosts[game_id]
            self.host_names.pop(game_id, None)
            del self.locks[game_id]
        else:
            lst = self.players.get(game_id, [])
            self.players[game_id] = [
                (ws, name) for ws, name in lst if ws is not websocket
            ]
            if not self.players[game_id]:
                del self.players[game_id]

    async def broadcast_state(self, game_id: str, state: dict) -> None:
        host_ws = self.hosts.get(game_id)
        players = list(state.get("scores", {}).keys())
        if host_ws:
            host_state = GameState(
                current_word=state.get("current_word"),
                expires_at=state.get("expires_at"),
                state=state.get("state"),
                remaining_words_count=len(state.get("remaining_words", [])),
                scores=state.get("scores", {}),
                players=players,
                current_correct=state.get("current_correct", 0),
                right_answers_to_advance=state.get("right_answers_to_advance", 1),
                current_master=state.get("current_master"),
            ).model_dump(mode="json")
            await host_ws.send_json(host_state)

            for ws, name in self.players.get(game_id, []):
                tries_per_player = state.get("tries_per_player", 0)
                attempts = state.get("player_attempts", {}).get(name, 0)
                tries_left = None
                if tries_per_player:
                    tries_left = max(tries_per_player - attempts, 0)

                word_for_player = state.get("current_word")

                pg_state = PlayerGameState(
                    expires_at=state["expires_at"],
                    state=state["state"],
                    remaining_words_count=len(state.get("remaining_words", [])),
                    scores=state.get("scores", {}),
                    players=players,
                    tries_left=tries_left,
                    current_word=word_for_player,
                    current_master=state.get("current_master"),
                ).model_dump(mode="json")

                await ws.send_json(pg_state)


manager = ConnectionManager()


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
                    "current_master": None,
                }
            },
            return_document=ReturnDocument.AFTER,
        )
        return updated_game

    new_word = game_before_pop["remaining_words"][-1]

    game_data = await games.find_one({"_id": game_id})
    current_master = game_data.get("current_master")
    if game_data.get("rotate_masters"):
        players = list(game_data.get("scores", {}).keys())
        current_master = choice(players) if players else None
    else:
        if not current_master:
            current_master = manager.host_names.get(game_id)

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
                "current_master": current_master,
            }
        },
        return_document=ReturnDocument.AFTER,
    )

    return updated_game
