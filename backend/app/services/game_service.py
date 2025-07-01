from asyncio import Lock
from datetime import datetime, timedelta, timezone
from random import choice
from typing import Optional

from fastapi import WebSocket
from pymongo import ReturnDocument

from backend.app.db import db
from backend.app.models import GameState, PlayerGameState, TeamStateForHost

games = db.games
decks = db.decks


def required_to_advance(team_state: dict) -> int: # Modified to accept team_state
    names = set(team_state.get("scores", {}).keys())
    names.discard(team_state.get("current_master"))
    players_count = len(names)
    return min(team_state.get("right_answers_to_advance", 1), players_count)


class ConnectionManager:
    def __init__(self) -> None:
        self.hosts: dict[str, WebSocket] = {}
        self.host_names: dict[str, str] = {}
        self.players: dict[str, list[tuple[WebSocket, str, str]]] = {} # Store (websocket, player_name, team_id)
        self.locks: dict[str, Lock] = {}

    async def connect_host(
        self, websocket: WebSocket, game_id: str, name: Optional[str]
    ) -> bool:
        if game_id in self.hosts:
            await websocket.close(
                code=1008, reason="Game already active and host is connected"
            )
            return False
        await websocket.accept()
        self.hosts[game_id] = websocket
        if name:
            self.host_names[game_id] = name
        self.locks[game_id] = Lock()
        return True

    async def connect_player(
        self, websocket: WebSocket, game_id: str, player_name: str, team_id: str # Added team_id
    ) -> bool:
        await websocket.accept()
        self.players.setdefault(game_id, []).append((websocket, player_name, team_id)) # Store team_id
        return True

    def disconnect(
        self, game_id: str, websocket: Optional[WebSocket] = None
    ) -> Optional[str]:
        if self.hosts.get(game_id) is websocket:
            del self.hosts[game_id]
            self.host_names.pop(game_id, None)
            self.locks.pop(game_id, None) # Remove lock when host disconnects
            return None

        removed_name = None
        lst = self.players.get(game_id, [])
        remaining: list[tuple[WebSocket, str, str]] = [] # Updated type hint
        for ws, name, team_id in lst: # Unpack team_id
            if ws is websocket:
                removed_name = name
            else:
                remaining.append((ws, name, team_id)) # Pack team_id

        if remaining:
            self.players[game_id] = remaining
        elif game_id in self.players:
            del self.players[game_id]

        return removed_name

    async def broadcast_state(self, game_id: str, game: dict) -> None: # Changed state to game
        host_ws = self.hosts.get(game_id)
        
        # Prepare host state
        host_teams_state = {}
        for team_id, team_data in game.get("teams", {}).items():
            host_teams_state[team_id] = TeamStateForHost(
                id=team_data["id"],
                name=team_data["name"],
                remaining_words_count=len(team_data.get("remaining_words", [])),
                current_word=team_data.get("current_word"),
                expires_at=team_data.get("expires_at"),
                current_master=team_data.get("current_master"),
                state=team_data.get("state"),
                scores=team_data.get("scores", {}),
                players=team_data.get("players", []),
                current_correct=team_data.get("current_correct", 0),
                right_answers_to_advance=game.get("right_answers_to_advance", 1), # From game level
            ).model_dump(mode="json")

        if host_ws:
            host_state = GameState(
                game_state=game.get("game_state"),
                teams=host_teams_state,
                winning_team=game.get("winning_team"),
            ).model_dump(mode="json")
            await host_ws.send_json(host_state)

        # Prepare player states
        all_teams_scores = {
            team_id: sum(team_data.get("scores", {}).values())
            for team_id, team_data in game.get("teams", {}).items()
        }

        for ws, player_name, player_team_id in self.players.get(game_id, []): # Unpack team_id
            team_data = game["teams"].get(player_team_id)
            if not team_data:
                continue # Should not happen if player is correctly connected to a team

            tries_per_player = game.get("tries_per_player", 0) # From game level
            attempts = team_data.get("player_attempts", {}).get(player_name, 0)
            tries_left = None
            if tries_per_player:
                tries_left = max(tries_per_player - attempts, 0)

            pg_state = PlayerGameState(
                game_state=game.get("game_state"),
                team_id=player_team_id,
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

            await ws.send_json(pg_state)


manager = ConnectionManager()


async def reassign_master(game_id: str, team_id: str) -> None:
    """Assign a new game master for a team if possible."""
    game = await games.find_one({"_id": game_id})
    if not game:
        return

    team_state = game.get("teams", {}).get(team_id)
    if not team_state:
        return

    players = team_state.get("players", [])
    if not players:
        new_master = None
    else:
        new_master = choice(players) if game.get("rotate_masters") else players[0]

    await games.update_one(
        {"_id": game_id},
        {"$set": {f"teams.{team_id}.current_master": new_master}},
    )


async def process_new_word(game_id: str, team_id: str, sec: int) -> dict: # Modified to accept team_id
    game = await games.find_one({"_id": game_id})
    if not game:
        return {} # Or raise an error

    team_state = game["teams"].get(team_id)
    if not team_state:
        return game # Or raise an error

    # Pop word from the specific team's remaining_words
    print(f"DEBUG: Before pop - team_id: {team_id}, remaining_words: {team_state.get('remaining_words')}")
    if team_state["remaining_words"]:
        new_word = team_state["remaining_words"].pop(0) # Pop from the beginning
    else:
        new_word = None

    # Update the team's state
    team_state["current_word"] = new_word
    print(f"DEBUG: After pop - new_word: {new_word}, remaining_words: {team_state.get('remaining_words')}")
    print(f"DEBUG: Before DB update - team_id: {team_id}, current_word: {team_state.get('current_word')}")
    team_state["expires_at"] = datetime.now(timezone.utc) + timedelta(seconds=sec) if new_word else None
    team_state["current_correct"] = 0
    team_state["player_attempts"] = {}
    team_state["correct_players"] = []

    # Game Master Selection for the team
    if game.get("rotate_masters"): # Multiple game masters mode
        players_in_team = team_state.get("players", [])
        if players_in_team:
            team_state["current_master"] = choice(players_in_team)
        else:
            team_state["current_master"] = None
    else: # Single game master mode for the team
        # The current_master for the team is set when the first player joins that team.
        # If it's not set yet, it means no one has joined this team or the first player hasn't been assigned.
        # We don't change it here if it's already set.
        if team_state["current_master"] is None and team_state["players"]:
            team_state["current_master"] = team_state["players"][0] # First player in the team

    if new_word is None:
        team_state["state"] = "finished"
        team_state["expires_at"] = None # No word, no expiration
    else:
        team_state["state"] = "in_progress" # Set state to in_progress when a new word is processed

    # Update the game document in MongoDB
    # Use $set to update the specific team within the 'teams' dictionary
    updated_game = await games.find_one_and_update(
        {"_id": game_id},
        {"$set": {f"teams.{team_id}": team_state}},
        return_document=ReturnDocument.AFTER,
    )

    # Check if this update finishes the overall game
    if updated_game and updated_game.get("game_state") != "finished":
        if team_state["state"] == "finished":
            updated_game["game_state"] = "finished"
            updated_game["winning_team"] = team_id
            await games.update_one(
                {"_id": game_id},
                {"$set": {"game_state": "finished", "winning_team": team_id}}
            )
        else:
            # See if any other team already finished
            for tid, t_state in updated_game["teams"].items():
                if t_state["state"] == "finished":
                    updated_game["game_state"] = "finished"
                    updated_game["winning_team"] = tid
                    await games.update_one(
                        {"_id": game_id},
                        {"$set": {"game_state": "finished", "winning_team": tid}}
                    )
                    break

    return updated_game
