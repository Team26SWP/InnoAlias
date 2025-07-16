from datetime import datetime, timezone
from random import shuffle
from fastapi.responses import Response
from pymongo import ReturnDocument
import asyncio
from fastapi import WebSocket, WebSocketDisconnect, APIRouter, HTTPException
from typing import Any

from backend.app.code_gen import generate_game_code
from backend.app.models import Game
from backend.app.services.game_service import (
    games,
    manager,
    process_new_word,
    required_to_advance,
    reassign_master,
    determine_winning_team,
)

router = APIRouter(prefix="", tags=["game"])


@router.post("/create")
async def create_game(game: Game):
    """Create a new game instance in the database."""
    words = list(game.deck)
    shuffle(words)

    if game.words_amount is not None and 1 < game.words_amount < len(words):
        words = words[: game.words_amount]

    code = await generate_game_code()

    teams_data: dict[str, dict[str, Any]] = {}
    for i in range(game.number_of_teams):
        team_id = f"team_{i+1}"
        team_name = f"Team {i+1}"

        team_words = list(words)
        shuffle(team_words)

        teams_data[team_id] = {
            "id": team_id,
            "name": team_name,
            "players": [],
            "remaining_words": team_words,
            "current_word": None,
            "expires_at": None,
            "current_master": None,
            "correct_players": [],
            "state": "pending",
            "scores": {},
            "player_attempts": {},
            "current_correct": 0,
            "right_answers_to_advance": game.right_answers_to_advance,
        }

    new_game = {
        "_id": code,
        "host_id": game.host_id,
        "number_of_teams": game.number_of_teams,
        "teams": teams_data,
        "deck": words,
        "words_amount": len(words),
        "time_for_guessing": game.time_for_guessing,
        "tries_per_player": game.tries_per_player,
        "right_answers_to_advance": game.right_answers_to_advance,
        "rotate_masters": game.rotate_masters,
        "game_state": "pending",
        "winning_team": None,
    }

    result = await games.insert_one(new_game)
    return {"id": str(result.inserted_id)}


@router.get("/leaderboard/{game_id}/export")
async def export_deck_txt(game_id: str):
    """Export the game's deck as a downloadable text file."""
    game = await games.find_one({"_id": game_id})
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    words = game.get("deck", [])
    content = "\n".join(words)
    timestamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    return Response(
        content=content,
        media_type="text/plain",
        headers={
            "Content-Disposition": f"attachment; filename=exported_deck_{timestamp}.txt"
        },
    )


@router.get("/deck/{game_id}")
async def get_game_deck(game_id: str):
    """Return the deck words for a given game."""
    game = await games.find_one({"_id": game_id})
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return {"words": game.get("deck", [])}


@router.websocket("/{game_id}")
async def _handle_start_game_action(game_id: str, game: dict[str, Any]):
    """Transition the game to the in-progress state and send updates."""
    await games.update_one(
        {"_id": game_id}, {"$set": {"game_state": "in_progress"}}
    )
    game["game_state"] = "in_progress"
    for tid in game["teams"]:
        if game["teams"][tid].get("state") == "pending" and game["teams"][
            tid
        ].get("remaining_words"):
            await process_new_word(game_id, tid, game["time_for_guessing"])
    refreshed = await games.find_one({"_id": game_id})
    if isinstance(refreshed, dict):
        await manager.broadcast_state(game_id, refreshed)


async def _handle_stop_game_action(game_id: str, game: dict[str, Any]):
    """Finish the game and broadcast the winner to clients."""
    winning_team = determine_winning_team(game)
    await games.update_one(
        {"_id": game_id},
        {
            "$set": {
                "game_state": "finished",
                "winning_team": winning_team,
            }
        },
    )
    game["game_state"] = "finished"
    game["winning_team"] = winning_team
    await manager.broadcast_state(game_id, game)


async def handle_game(websocket: WebSocket, game_id: str):
    """Main WebSocket endpoint for the host controlling the game."""
    host_id = websocket.query_params.get("id")
    if host_id is None or not await games.find_one(
        {"_id": game_id, "host_id": host_id}
    ):
        await websocket.close(
            code=1011, reason="Game not found or not authorized as host"
        )
        return

    assert host_id is not None

    if not await manager.connect_host(websocket, game_id):
        return

    timer_task = asyncio.create_task(check_timers(game_id))

    try:
        game_data = await games.find_one({"_id": game_id})
        if not isinstance(game_data, dict):
            return
        await manager.broadcast_state(game_id, game_data)

        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            game_lookup = await games.find_one({"_id": game_id})
            if (
                not isinstance(game_lookup, dict)
                or game_lookup.get("game_state") == "finished"
            ):
                break
            game = game_lookup

            if action == "start_game" and game["game_state"] == "pending":
                await _handle_start_game_action(game_id, game)

            elif action == "stop_game":
                await _handle_stop_game_action(game_id, game)
                break

    except (WebSocketDisconnect, Exception) as e:
        print(f"Host disconnected or error in handle_game for {game_id}: {e}")
    finally:
        timer_task.cancel()
        # Disconnect host
        manager.disconnect(game_id, websocket)

        # Disconnect all players associated with this game
        if game_id in manager.players:
            for player_websocket, _, _ in manager.players[game_id]:
                await player_websocket.close(
                    code=1000,
                    reason="Host disconnected, closing player connection",
                )
            manager.players.pop(
                game_id, None
            )  # Remove all players for this game

        # Delete the game from the database
        await games.delete_one({"_id": game_id})
        print(f"Game {game_id} deleted due to host disconnection.")


async def check_timers(game_id: str):
    """Continuously check word timers and advance teams when expired."""
    while True:
        try:
            game_data = await games.find_one({"_id": game_id})
            if (
                not isinstance(game_data, dict)
                or game_data.get("game_state") != "in_progress"
            ):
                await asyncio.sleep(1)
                continue

            now = datetime.now(timezone.utc)

            expirations = [
                team.get("expires_at")
                for team in game_data.get("teams", {}).values()
                if team.get("expires_at")
            ]

            expired_teams = [
                team_id
                for team_id, team_data in game_data.get("teams", {}).items()
                if team_data.get("expires_at")
                and now >= team_data["expires_at"].replace(tzinfo=timezone.utc)
            ]

            if expired_teams:
                async with manager.locks.get(game_id, asyncio.Lock()):
                    for team_id in expired_teams:
                        current_game = await games.find_one({"_id": game_id})
                        if not isinstance(current_game, dict):
                            continue
                        current_expires_at = current_game["teams"][
                            team_id
                        ].get("expires_at")
                        if (
                            current_expires_at
                            and now
                            >= current_expires_at.replace(tzinfo=timezone.utc)
                        ):
                            new_state = await process_new_word(
                                game_id,
                                team_id,
                                game_data["time_for_guessing"],
                            )
                            await manager.broadcast_state(game_id, new_state)
                continue

            if expirations:
                next_expiry = min(expirations)
                sleep_duration = (
                    next_expiry.replace(tzinfo=timezone.utc) - now
                ).total_seconds()
                if sleep_duration > 0:
                    await asyncio.sleep(sleep_duration)
            else:
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            break
        except Exception as e:
            print(e)
            await asyncio.sleep(5)


@router.get("/leaderboard/{game_id}")
async def get_leaderboard(game_id: str):
    """Return a leaderboard with team and player scores."""
    game = await games.find_one({"_id": game_id})
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    team_scores = {
        team_data["name"]: sum(team_data.get("scores", {}).values())
        for team_id, team_data in game.get("teams", {}).items()
    }
    sorted_teams = dict(
        sorted(team_scores.items(), key=lambda item: item[1], reverse=True)
    )

    detailed_leaderboard = {}
    for team_name, total_score in sorted_teams.items():
        team_id = next(
            (
                tid
                for tid, tdata in game["teams"].items()
                if tdata["name"] == team_name
            ),
            None,
        )
        if team_id:
            team_data = game["teams"][team_id]
            detailed_leaderboard[team_name] = {
                "total_score": total_score,
                "players": dict(
                    sorted(
                        team_data.get("scores", {}).items(),
                        key=lambda item: item[1],
                        reverse=True,
                    )
                ),
            }
    return detailed_leaderboard


@router.delete("/delete/{game_id}")
async def delete_game(game_id: str):
    """Remove a game from the database."""
    if not await games.find_one_and_delete({"_id": game_id}):
        raise HTTPException(status_code=404, detail="Game not found")
    return {"status": "OK"}


@router.websocket("/player/{game_id}")
async def _handle_switch_team(
    game_id: str,
    player_name: str,
    team_id: str,
    data: dict[str, Any],
    websocket: WebSocket,
) -> str:
    """Move a player to another team if the request is valid."""
    new_team_id = data.get("new_team_id")
    game = await games.find_one({"_id": game_id})
    if (
        not isinstance(game, dict)
        or not new_team_id
        or new_team_id == team_id
        or new_team_id not in game["teams"]
    ):
        return team_id

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

    await games.update_one(
        {"_id": game_id},
        {
            "$addToSet": {f"teams.{new_team_id}.players": player_name},
            "$set": {f"teams.{new_team_id}.scores.{player_name}": 0},
        },
    )
    manager.switch_player_team(game_id, player_name, new_team_id, websocket)

    new_game_state = await games.find_one({"_id": game_id})
    if (
        isinstance(new_game_state, dict)
        and not new_game_state.get("rotate_masters")
        and not new_game_state["teams"][new_team_id].get("current_master")
    ):
        await games.update_one(
            {"_id": game_id, f"teams.{new_team_id}.current_master": None},
            {"$set": {f"teams.{new_team_id}.current_master": player_name}},
        )
    refreshed_state = await games.find_one({"_id": game_id})
    if isinstance(refreshed_state, dict):
        await manager.broadcast_state(game_id, refreshed_state)
    return new_team_id


async def _handle_skip_action(
    game_id: str, team_id: str, time_for_guessing: int
):
    """Skip the current word and send the next one."""
    async with manager.locks[game_id]:
        new_state = await process_new_word(game_id, team_id, time_for_guessing)
    await manager.broadcast_state(game_id, new_state)


async def _handle_guess_action(
    game_id: str,
    player_name: str,
    team_id: str,
    data: dict[str, Any],
    game: dict[str, Any],
):
    """Process a player's guess and update scores if correct."""
    guess = data.get("guess", "").strip().lower()
    team_state = game["teams"][team_id]

    can_guess = (
        team_state.get("state") == "in_progress"
        and team_state.get("current_master") != player_name
        and player_name not in team_state.get("correct_players", [])
    )

    if not can_guess:
        return

    tries_per_player = game.get("tries_per_player", 0)
    if tries_per_player > 0:
        attempts = team_state.get("player_attempts", {}).get(player_name, 0)
        if attempts >= tries_per_player:
            return

    expires_at = team_state.get("expires_at")
    if expires_at and datetime.now(timezone.utc) > expires_at.replace(
        tzinfo=timezone.utc
    ):
        return

    async with manager.locks[game_id]:
        await games.update_one(
            {"_id": game_id},
            {"$inc": {f"teams.{team_id}.player_attempts.{player_name}": 1}},
        )

        if guess == team_state.get("current_word", "").lower():
            updated_game = await games.find_one_and_update(
                {"_id": game_id},
                {
                    "$inc": {
                        f"teams.{team_id}.scores.{player_name}": 1,
                        f"teams.{team_id}.current_correct": 1,
                    },
                    "$addToSet": {
                        f"teams.{team_id}.correct_players": player_name
                    },
                },
                return_document=ReturnDocument.AFTER,
            )
            if isinstance(updated_game, dict) and updated_game["teams"][
                team_id
            ]["current_correct"] >= required_to_advance(
                updated_game["teams"][team_id]
            ):
                updated_game = await process_new_word(
                    game_id, team_id, game["time_for_guessing"]
                )
            if isinstance(updated_game, dict):
                await manager.broadcast_state(game_id, updated_game)
        else:
            refreshed = await games.find_one({"_id": game_id})
            if isinstance(refreshed, dict):
                await manager.broadcast_state(game_id, refreshed)


async def _handle_player_disconnect(
    game_id: str, player_name: str, team_id: str
):
    """Clean up state when a player disconnects."""
    game = await games.find_one({"_id": game_id})
    if isinstance(game, dict):
        await games.update_one(
            {"_id": game_id},
            {
                "$pull": {f"teams.{team_id}.players": player_name},
                "$unset": {f"teams.{team_id}.scores.{player_name}": ""},
            },
        )
        if (
            game.get("game_state") != "finished"
            and game["teams"][team_id].get("current_master") == player_name
        ):
            await reassign_master(game_id, team_id)
        refreshed = await games.find_one({"_id": game_id})
        if isinstance(refreshed, dict):
            await manager.broadcast_state(game_id, refreshed)


async def handle_player(websocket: WebSocket, game_id: str):
    """WebSocket endpoint for players participating in the game."""
    player_name = websocket.query_params.get("name")
    team_id = websocket.query_params.get("team_id")
    if not player_name or not team_id:
        await websocket.close(
            code=1008, reason="Missing player's name or team ID"
        )
        return

    game_data = await games.find_one({"_id": game_id})
    if not isinstance(game_data, dict) or team_id not in game_data["teams"]:
        await websocket.close(code=1011, reason="Game or team not found")
        return

    if game_data.get("game_state") == "in_progress":
        await websocket.close(code=1011, reason="Game is already in progress")
        return

    await manager.connect_player(websocket, game_id, player_name, team_id)
    await games.update_one(
        {"_id": game_id, f"teams.{team_id}.players": {"$ne": player_name}},
        {"$addToSet": {f"teams.{team_id}.players": player_name}},
    )
    await games.update_one(
        {
            "_id": game_id,
            f"teams.{team_id}.scores.{player_name}": {"$exists": False},
        },
        {"$set": {f"teams.{team_id}.scores.{player_name}": 0}},
    )

    game = await games.find_one({"_id": game_id})
    if (
        isinstance(game, dict)
        and not game.get("rotate_masters")
        and not game["teams"][team_id].get("current_master")
    ):
        await games.update_one(
            {"_id": game_id, f"teams.{team_id}.current_master": None},
            {"$set": {f"teams.{team_id}.current_master": player_name}},
        )

    try:
        current_state = await games.find_one({"_id": game_id})
        if isinstance(current_state, dict):
            await manager.broadcast_state(game_id, current_state)

        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            game_lookup = await games.find_one({"_id": game_id})
            if (
                not isinstance(game_lookup, dict)
                or game_lookup.get("game_state") == "finished"
            ):
                break
            game = game_lookup

            if action == "switch_team" and game["game_state"] == "pending":
                team_id = await _handle_switch_team(
                    game_id, player_name, team_id, data, websocket
                )

            elif (
                action == "skip"
                and game["teams"][team_id].get("current_master") == player_name
            ):
                await _handle_skip_action(
                    game_id, team_id, game["time_for_guessing"]
                )

            elif action == "guess":
                await _handle_guess_action(
                    game_id, player_name, team_id, data, game
                )

    except (WebSocketDisconnect, Exception) as e:
        print(f"Player {player_name} disconnected or error: {e}")
    finally:
        manager.disconnect(game_id, websocket)
        await _handle_player_disconnect(game_id, player_name, team_id)
