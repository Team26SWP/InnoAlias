from asyncio import Lock
from datetime import datetime, timedelta, timezone
from random import choice
from typing import Optional, Tuple, Any, Dict, cast

from fastapi import WebSocket
from pymongo import ReturnDocument
from backend.app.db import db
from backend.app.models import GameState, PlayerGameState, TeamStateForHost

games = db.games
decks = db.decks


def required_to_advance(team_state: dict) -> int:
    names = set(team_state.get("scores", {}).keys())
    names.discard(team_state.get("current_master"))
    return min(team_state.get("right_answers_to_advance", 1), len(names))


class ConnectionManager:
    def __init__(self) -> None:
        self.hosts: dict[str, WebSocket] = {}
        self.players: dict[str, list[Tuple[WebSocket, str, str]]] = {}
        self.locks: dict[str, Lock] = {}

    async def connect_host(self, websocket: WebSocket, game_id: str) -> bool:
        if game_id in self.hosts:
            await websocket.close(code=1008, reason="Host already connected")
            return False
        await websocket.accept()
        self.hosts[game_id] = websocket
        self.locks[game_id] = Lock()
        return True

    async def connect_player(
        self, websocket: WebSocket, game_id: str, player_name: str, team_id: str
    ) -> None:
        await websocket.accept()
        self.players.setdefault(game_id, []).append((websocket, player_name, team_id))

    def disconnect(self, game_id: str, websocket: WebSocket) -> Optional[str]:
        if self.hosts.get(game_id) is websocket:
            del self.hosts[game_id]
            self.locks.pop(game_id, None)
            return None

        removed_player = None
        if game_id in self.players:
            remaining_players = []
            for conn in self.players[game_id]:
                if conn[0] is websocket:
                    removed_player = conn[1]
                else:
                    remaining_players.append(conn)
            self.players[game_id] = remaining_players
        return removed_player

    def switch_player_team(
        self, game_id: str, player_name: str, new_team_id: str, websocket: WebSocket
    ):
        if game_id in self.players:
            for i, (ws, name, team_id) in enumerate(self.players[game_id]):
                if ws is websocket and name == player_name:
                    self.players[game_id][i] = (ws, name, new_team_id)
                    break

    async def broadcast_state(self, game_id: str, game: Dict[str, Any]) -> None:
        if host_ws := self.hosts.get(game_id):
            host_teams_state = {
                team_id: TeamStateForHost(
                    **team_data,
                    remaining_words_count=len(team_data.get("remaining_words", [])),
                )
                for team_id, team_data in game.get("teams", {}).items()
            }
            host_state = GameState(
                game_state=game.get("game_state", "pending"),
                teams=host_teams_state,
                winning_team=game.get("winning_team"),
            ).model_dump(mode="json")
            await host_ws.send_json(host_state)

        all_teams_scores = {
            t["name"]: sum(t.get("scores", {}).values())
            for t in game.get("teams", {}).values()
        }
        for ws, name, p_team_id in self.players.get(game_id, []):
            if not (team_data := game["teams"].get(p_team_id)):
                continue

            attempts = team_data.get("player_attempts", {}).get(name, 0)
            tries_left = (
                (game["tries_per_player"] - attempts)
                if game.get("tries_per_player", 0) > 0
                else None
            )

            player_state = PlayerGameState(
                game_state=game.get("game_state", "pending"),
                team_id=p_team_id,
                team_name=team_data.get("name"),
                expires_at=team_data.get("expires_at"),
                remaining_words_count=len(team_data.get("remaining_words", [])),
                tries_left=tries_left,
                current_word=team_data.get("current_word"),
                current_master=team_data.get("current_master"),
                team_scores=team_data.get("scores", {}),
                all_teams_scores=all_teams_scores,
                players_in_team=team_data.get("players", []),
                winning_team=game.get("winning_team"),
            ).model_dump(mode="json")
            await ws.send_json(player_state)


manager = ConnectionManager()


async def add_player_to_game(game_id: str, player_name: str, team_id: str):
    await games.update_one(
        {"_id": game_id, f"teams.{team_id}.players": {"$ne": player_name}},
        {"$addToSet": {f"teams.{team_id}.players": player_name}},
    )
    await games.update_one(
        {"_id": game_id, f"teams.{team_id}.scores.{player_name}": {"$exists": False}},
        {"$set": {f"teams.{team_id}.scores.{player_name}": 0}},
    )
    game = cast(Dict[str, Any], await games.find_one({"_id": game_id}))
    if not game.get("rotate_masters") and not game["teams"][team_id].get(
        "current_master"
    ):
        await games.update_one(
            {"_id": game_id, f"teams.{team_id}.current_master": None},
            {"$set": {f"teams.{team_id}.current_master": player_name}},
        )
    return await games.find_one({"_id": game_id})


async def remove_player_from_game(game_id: str, player_name: str, team_id: str):
    game = cast(Dict[str, Any], await games.find_one({"_id": game_id}))
    if not game:
        return None

    await games.update_one(
        {"_id": game_id},
        {
            "$pull": {f"teams.{team_id}.players": player_name},
            "$unset": {
                f"teams.{team_id}.scores.{player_name}": "",
                f"teams.{team_id}.player_attempts.{player_name}": "",
            },
        },
    )
    if game["teams"][team_id].get("current_master") == player_name:
        await reassign_master(game_id, team_id)
    return await games.find_one({"_id": game_id})


async def reassign_master(game_id: str, team_id: str):
    game = await games.find_one({"_id": game_id})
    if not game or not (team_state := game.get("teams", {}).get(team_id)):
        return

    players = team_state.get("players", [])
    new_master = (
        (choice(players) if game.get("rotate_masters") else players[0])
        if players
        else None
    )
    await games.update_one(
        {"_id": game_id}, {"$set": {f"teams.{team_id}.current_master": new_master}}
    )


def determine_winning_team(game: Dict[str, Any]) -> Optional[str]:
    team_scores = {
        tid: sum(t.get("scores", {}).values())
        for tid, t in game.get("teams", {}).items()
    }
    if not team_scores:
        return None

    max_score = -1
    winning_teams = []
    for team_id, score in team_scores.items():
        if score > max_score:
            max_score = score
            winning_teams = [team_id]
        elif score == max_score:
            winning_teams.append(team_id)

    if len(winning_teams) == 1:
        return winning_teams[0]
    else:
        # Handle ties by checking remaining words, fewest wins
        min_remaining_words = float("inf")
        final_winner = None
        for team_id in winning_teams:
            remaining_words_count = len(
                game.get("teams", {}).get(team_id, {}).get("remaining_words", [])
            )
            if remaining_words_count < min_remaining_words:
                min_remaining_words = remaining_words_count
                final_winner = team_id
        return final_winner


async def process_new_word(game_id: str, team_id: str, sec: int) -> Dict[str, Any]:
    game = cast(Dict[str, Any], await games.find_one({"_id": game_id}))
    team_state = game["teams"][team_id]

    new_word = (
        team_state["remaining_words"].pop(0)
        if team_state.get("remaining_words")
        else None
    )
    team_state.update(
        {
            "current_word": new_word,
            "expires_at": (
                datetime.now(timezone.utc) + timedelta(seconds=sec)
                if new_word
                else None
            ),
            "current_correct": 0,
            "player_attempts": {},
            "correct_players": [],
            "state": "in_progress" if new_word else "finished",
        }
    )

    if game.get("rotate_masters") and team_state["players"]:
        team_state["current_master"] = choice(team_state["players"])
    elif not team_state.get("current_master") and team_state["players"]:
        team_state["current_master"] = team_state["players"][0]

    updated_game = cast(
        Dict[str, Any],
        await games.find_one_and_update(
            {"_id": game_id},
            {"$set": {f"teams.{team_id}": team_state}},
            return_document=ReturnDocument.AFTER,
        ),
    )

    if all(
        t.get("state") == "finished" for t in updated_game.get("teams", {}).values()
    ):
        winning_team_id = determine_winning_team(updated_game)
        await games.update_one(
            {"_id": game_id},
            {"$set": {"game_state": "finished", "winning_team": winning_team_id}},
        )
        updated_game = cast(Dict[str, Any], await games.find_one({"_id": game_id}))

    return updated_game
