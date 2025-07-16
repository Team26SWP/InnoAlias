"""Service layer handling in-memory game state and WebSocket interactions."""

from asyncio import Lock
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import WebSocket
from pymongo import ReturnDocument

from backend.app.db import db
from backend.app.models import GameState, PlayerGameState, TeamStateForHost

"""Helper utilities and connection management for multiplayer games."""

games = db.games
decks = db.decks


def required_to_advance(team_state: dict) -> int:
    """Calculate how many correct answers are needed for a team to advance."""
    names = set(team_state.get("scores", {}).keys())
    names.discard(team_state.get("current_master"))
    return min(team_state.get("right_answers_to_advance", 1), max(1, len(names)))


class ConnectionManager:
    """Manage WebSocket connections for hosts and players."""

    def __init__(self) -> None:
        self.hosts: dict[str, WebSocket] = {}
        self.players: dict[str, list[tuple[WebSocket, str, str]]] = {}
        self.locks: dict[str, Lock] = {}

    async def connect_host(self, websocket: WebSocket, game_id: str) -> bool:
        """Register a host connection for a game."""
        if game_id in self.hosts:
            await websocket.close(code=1008, reason="Host already connected")
            return False
        await websocket.accept()
        self.hosts[game_id] = websocket
        self.locks[game_id] = Lock()
        return True

    async def connect_player(
        self,
        websocket: WebSocket,
        game_id: str,
        player_name: str,
        team_id: str,
    ) -> None:
        """Add a player connection to the manager."""
        await websocket.accept()
        self.players.setdefault(game_id, []).append((websocket, player_name, team_id))

    def disconnect(self, game_id: str, websocket: WebSocket) -> str | None:
        """Remove a connection and return the player name if applicable."""
        if self.hosts.get(game_id) is websocket:
            self.hosts.pop(game_id, None)
            self.locks.pop(game_id, None)
            return None
        return self._remove_player_connection(game_id, websocket)

    def _remove_player_connection(
        self, game_id: str, websocket: WebSocket
    ) -> str | None:
        """Helper to remove a player connection from internal storage."""
        removed_player = None
        if game_id in self.players:
            initial_players = self.players[game_id]
            player_to_remove = next(
                (conn for conn in initial_players if conn[0] is websocket), None
            )
            if player_to_remove:
                removed_player = player_to_remove[1]
                self.players[game_id].remove(player_to_remove)
        return removed_player

    def switch_player_team(
        self,
        game_id: str,
        player_name: str,
        new_team_id: str,
        websocket: WebSocket,
    ):
        """Update player's team association in manager."""
        if game_id in self.players:
            for i, (ws, name, _team_id) in enumerate(self.players[game_id]):
                if ws is websocket and name == player_name:
                    self.players[game_id][i] = (ws, name, new_team_id)
                    break

    async def broadcast_state(self, game_id: str, game: dict[str, Any] | None) -> None:
        """Send the updated game state to all connected clients."""
        if not game:
            return
        await self._broadcast_host_state(game_id, game)
        await self._broadcast_player_state(game_id, game)

    async def _broadcast_host_state(self, game_id: str, game: dict[str, Any]) -> None:
        """Send the game state tailored for the host."""
        if host_ws := self.hosts.get(game_id):
            try:
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
            except Exception as e:
                print(f"Error broadcasting to host for game {game_id}: {e}")

    async def _broadcast_player_state(self, game_id: str, game: dict[str, Any]) -> None:
        """Send each player their personalised view of the game state."""
        all_teams_scores = {
            t["name"]: sum(t.get("scores", {}).values())
            for t in game.get("teams", {}).values()
        }
        if game_id not in self.players:
            return

        for ws, name, p_team_id in self.players.get(game_id, []):
            if not (team_data := game["teams"].get(p_team_id)):
                continue
            try:
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
            except Exception as e:
                print(f"Error broadcasting to player {name} for game {game_id}: {e}")


manager = ConnectionManager()


async def add_player_to_game(
    game_id: str, player_name: str, team_id: str
) -> dict[str, Any] | None:
    """Add a player to the specified team and initialise their score."""
    game = await games.find_one({"_id": game_id})
    if not game:
        return None

    update_query: dict[str, dict[str, Any]] = {
        "$addToSet": {f"teams.{team_id}.players": player_name},
        "$set": {f"teams.{team_id}.scores.{player_name}": 0},
    }

    # Set player as master if they are the first player and rotate_masters is false
    if (
        not game.get("rotate_masters")
        and not game.get("teams", {}).get(team_id, {}).get("current_master")
        and not game.get("teams", {}).get(team_id, {}).get("players")
    ):
        update_query["$set"][f"teams.{team_id}.current_master"] = player_name

    return await games.find_one_and_update(
        {"_id": game_id, f"teams.{team_id}.players": {"$ne": player_name}},
        update_query,
        return_document=ReturnDocument.AFTER,
    )


async def remove_player_from_game(
    game_id: str, player_name: str, team_id: str
) -> dict[str, Any] | None:
    """Remove a player from the team and reassign the master if needed."""
    async with manager.locks.get(game_id, Lock()):
        game = await games.find_one({"_id": game_id})
        if not game or team_id not in game.get("teams", {}):
            return None

        update_query: dict[str, dict[str, Any]] = {
            "$pull": {f"teams.{team_id}.players": player_name},
            "$unset": {
                f"teams.{team_id}.scores.{player_name}": "",
                f"teams.{team_id}.player_attempts.{player_name}": "",
            },
        }

        team = game["teams"][team_id]
        if team.get("current_master") == player_name:
            players = team.get("players", [])
            new_master = None
            if player_name in players:
                current_index = players.index(player_name)
                players.remove(player_name)
                if players:
                    if game.get("rotate_masters"):
                        new_master = players[current_index % len(players)]
                    else:
                        new_master = players[0]
            update_query["$set"] = {f"teams.{team_id}.current_master": new_master}

        return await games.find_one_and_update(
            {"_id": game_id},
            update_query,
            return_document=ReturnDocument.AFTER,
        )


async def reassign_master(game_id: str, team_id: str) -> dict[str, Any] | None:
    """Choose a new master for the team based on rotation settings."""
    async with manager.locks.get(game_id, Lock()):
        game = await games.find_one({"_id": game_id})
        if not game or not (team_state := game.get("teams", {}).get(team_id)):
            return None

        players = team_state.get("players", [])
        new_master = None
        if players:
            if game.get("rotate_masters"):
                current_master = team_state.get("current_master")
                if current_master in players:
                    current_index = players.index(current_master)
                    new_master = players[(current_index + 1) % len(players)]
                else:
                    new_master = players[0]
            else:
                new_master = players[0]

        return await games.find_one_and_update(
            {"_id": game_id},
            {"$set": {f"teams.{team_id}.current_master": new_master}},
            return_document=ReturnDocument.AFTER,
        )


def determine_winning_team(game: dict[str, Any]) -> str | None:
    """Determine the team with the highest score."""
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

    return _handle_tie_breaking(game, winning_teams)


def _handle_tie_breaking(game: dict[str, Any], winning_teams: list[str]) -> str | None:
    """Select a winner based on remaining words when scores tie."""
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


async def process_new_word(
    game_id: str, team_id: str, sec: int
) -> dict[str, Any] | None:
    """Move the team to the next word and update timers. This operation is atomic."""
    async with manager.locks.get(game_id, Lock()):
        game = await games.find_one({"_id": game_id})
        if not game or team_id not in game["teams"]:
            return None

        team_state = game["teams"][team_id]

        new_word = (
            team_state["remaining_words"].pop(0)
            if team_state.get("remaining_words")
            else None
        )

        team_state["current_word"] = new_word
        team_state["expires_at"] = (
            (datetime.now(UTC) + timedelta(seconds=sec)) if new_word else None
        )
        team_state["current_correct"] = 0
        team_state["player_attempts"] = {}
        team_state["correct_players"] = []
        team_state["state"] = "in_progress" if new_word else "finished"

        _assign_current_master(game, team_state)

        updated_game = await games.find_one_and_update(
            {"_id": game_id},
            {"$set": {f"teams.{team_id}": team_state}},
            return_document=ReturnDocument.AFTER,
        )

        if updated_game:
            return await _check_and_set_game_finished(game_id, updated_game)
        return None


def _assign_current_master(game: dict[str, Any], team_state: dict[str, Any]):
    """Ensure the team has a current master assigned."""
    players = team_state.get("players", [])
    if not players:
        team_state["current_master"] = None
        return

    current_master = team_state.get("current_master")
    if game.get("rotate_masters"):
        if current_master in players:
            current_index = players.index(current_master)
            team_state["current_master"] = players[(current_index + 1) % len(players)]
        else:
            team_state["current_master"] = players[0]
    elif not current_master:
        team_state["current_master"] = players[0]


async def _check_and_set_game_finished(
    game_id: str, updated_game: dict[str, Any]
) -> dict[str, Any]:
    """Update game state to finished if all teams are done."""
    if all(
        t.get("state") == "finished" for t in updated_game.get("teams", {}).values()
    ):
        winning_team_id = determine_winning_team(updated_game)
        finished_game = await games.find_one_and_update(
            {"_id": game_id},
            {
                "$set": {
                    "game_state": "finished",
                    "winning_team": winning_team_id,
                }
            },
            return_document=ReturnDocument.AFTER,
        )
        return finished_game or updated_game
    return updated_game


async def get_game_state(game_id: str) -> dict[str, Any] | None:
    """Retrieve the current state of a game."""
    return await games.find_one({"_id": game_id})
