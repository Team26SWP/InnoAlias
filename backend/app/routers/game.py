from datetime import datetime, timezone
from random import shuffle
from fastapi.responses import Response
from pymongo import ReturnDocument
import asyncio
from fastapi import WebSocket, WebSocketDisconnect, APIRouter, HTTPException
from typing import Any, Dict, Optional

from backend.app.code_gen import generate_game_code
from backend.app.models import Game
from backend.app.services.game_service import (
    games,
    manager,
    process_new_word,
    required_to_advance,
    reassign_master,
    determine_winning_team,
    remove_player_from_game,
    add_player_to_game,
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


async def _handle_start_game_action(game_id: str, game: dict[str, Any]):
    """Transition the game to the in-progress state and send updates."""
    updated_game = await games.find_one_and_update(
        {"_id": game_id, "game_state": "pending"},
        {"$set": {"game_state": "in_progress"}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated_game:
        return

    for tid in updated_game.get("teams", {}):
        if updated_game["teams"][tid].get("state") == "pending" and updated_game["teams"][tid].get("remaining_words"):
            updated_game = await process_new_word(game_id, tid, updated_game["time_for_guessing"])

    await manager.broadcast_state(game_id, updated_game)


async def _handle_stop_game_action(game_id: str, game: dict[str, Any]):
    """Finish the game and broadcast the winner to clients."""
    winning_team = determine_winning_team(game)
    updated_game = await games.find_one_and_update(
        {"_id": game_id},
        {
            "$set": {
                "game_state": "finished",
                "winning_team": winning_team,
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    await manager.broadcast_state(game_id, updated_game)


@router.websocket("/{game_id}")
async def handle_game(websocket: WebSocket, game_id: str):
    """Main WebSocket endpoint for the host controlling the game."""
    game = await games.find_one({"_id": game_id})
    if not game:
        await websocket.close(code=1011, reason="Game not found")
        return

    if not await manager.connect_host(websocket, game_id):
        return

    timer_task = asyncio.create_task(check_timers(game_id))
    game_state = game.get("game_state", "pending")

    try:
        await manager.broadcast_state(game_id, game)

        while game_state != "finished":
            data = await websocket.receive_json()
            action = data.get("action")

            current_game = await games.find_one({"_id": game_id})
            if not current_game or current_game.get("game_state") == "finished":
                break
            
            game_state = current_game.get("game_state")

            if action == "start_game" and game_state == "pending":
                await _handle_start_game_action(game_id, current_game)
            elif action == "stop_game":
                await _handle_stop_game_action(game_id, current_game)
                break

    except (WebSocketDisconnect, Exception) as e:
        print(f"Host disconnected or error in handle_game for {game_id}: {e}")
    finally:
        timer_task.cancel()
        manager.disconnect(game_id, websocket)

        game = await games.find_one({"_id": game_id})
        if game and game.get("game_state") == "pending":
            if game_id in manager.players:
                for player_websocket, _, _ in manager.players[game_id]:
                    await player_websocket.close(
                        code=1000,
                        reason="Host disconnected, closing player connection",
                    )
                manager.players.pop(game_id, None)
            await games.delete_one({"_id": game_id})
            print(f"Game {game_id} deleted due to host disconnection during pending state.")


async def check_timers(game_id: str):
    """Continuously check word timers and advance teams when expired."""
    while True:
        try:
            game_data = await games.find_one({"_id": game_id})
            if not game_data or game_data.get("game_state") != "in_progress":
                await asyncio.sleep(1)
                continue

            now = datetime.now(timezone.utc)
            
            next_expiry = None
            for team in game_data.get("teams", {}).values():
                if expires_at := team.get("expires_at"):
                    if now >= expires_at.replace(tzinfo=timezone.utc):
                        async with manager.locks.get(game_id, asyncio.Lock()):
                            # Re-fetch inside lock to ensure atomicity
                            refreshed_game = await games.find_one({"_id": game_id})
                            if refreshed_game and refreshed_game["teams"][team["id"]].get("expires_at") == expires_at:
                                new_state = await process_new_word(
                                    game_id,
                                    team["id"],
                                    game_data["time_for_guessing"],
                                )
                                await manager.broadcast_state(game_id, new_state)
                    elif not next_expiry or expires_at < next_expiry:
                        next_expiry = expires_at
            
            if next_expiry:
                sleep_duration = (next_expiry.replace(tzinfo=timezone.utc) - now).total_seconds()
                if sleep_duration > 0:
                    await asyncio.sleep(sleep_duration)
            else:
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Error in check_timers for game {game_id}: {e}")
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
            (tid for tid, tdata in game["teams"].items() if tdata["name"] == team_name),
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


async def _handle_switch_team(
    game_id: str,
    player_name: str,
    team_id: str,
    data: dict[str, Any],
    websocket: WebSocket,
) -> str:
    """Move a player to another team if the request is valid."""
    new_team_id = data.get("new_team_id")
    if not new_team_id or new_team_id == team_id:
        return team_id

    async with manager.locks.get(game_id, asyncio.Lock()):
        game = await games.find_one({"_id": game_id})
        if not game or new_team_id not in game["teams"]:
            return team_id

        # Remove from old team
        team = game["teams"][team_id]
        if player_name not in team.get("players", []):
            return team_id # Player not in team

        pull_query = {
            f"teams.{team_id}.players": player_name,
        }
        unset_query = {
            f"teams.{team_id}.scores.{player_name}": "",
            f"teams.{team_id}.player_attempts.{player_name}": "",
        }
        
        update_pipeline = {"$pull": pull_query, "$unset": unset_query}

        if team.get("current_master") == player_name:
            players = team.get("players", [])
            players.remove(player_name)
            new_master = None
            if players:
                new_master = choice(players) if game.get("rotate_masters") else players[0]
            update_pipeline["$set"] = {f"teams.{team_id}.current_master": new_master}
        
        await games.update_one({"_id": game_id}, update_pipeline)

        # Add to new team
        push_query = {f"teams.{new_team_id}.players": player_name}
        set_query = {f"teams.{new_team_id}.scores.{player_name}": 0}
        
        new_team_players = game["teams"][new_team_id].get("players", [])
        if not game.get("rotate_masters") and not game["teams"][new_team_id].get("current_master") and not new_team_players:
            set_query[f"teams.{new_team_id}.current_master"] = player_name

        await games.update_one(
            {"_id": game_id},
            {"$addToSet": push_query, "$set": set_query},
        )
        
        manager.switch_player_team(game_id, player_name, new_team_id, websocket)

    refreshed_state = await games.find_one({"_id": game_id})
    await manager.broadcast_state(game_id, refreshed_state)
    return new_team_id


async def _handle_skip_action(game_id: str, team_id: str, time_for_guessing: int):
    """Skip the current word and send the next one."""
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

    # Increment attempts first
    await games.update_one(
        {"_id": game_id},
        {"$inc": {f"teams.{team_id}.player_attempts.{player_name}": 1}},
    )

    if guess == team_state.get("current_word", "").lower():
        async with manager.locks.get(game_id, asyncio.Lock()):
            # Re-fetch game state inside lock
            current_game = await games.find_one({"_id": game_id})
            if not current_game: return
            
            team_state = current_game["teams"][team_id]
            # Check if player has already guessed correctly in another request
            if player_name in team_state.get("correct_players", []):
                return

            updated_game = await games.find_one_and_update(
                {"_id": game_id},
                {
                    "$inc": {
                        f"teams.{team_id}.scores.{player_name}": 1,
                        f"teams.{team_id}.current_correct": 1,
                    },
                    "$addToSet": {f"teams.{team_id}.correct_players": player_name},
                },
                return_document=ReturnDocument.AFTER,
            )
            if updated_game and updated_game["teams"][team_id]["current_correct"] >= required_to_advance(updated_game["teams"][team_id]):
                updated_game = await process_new_word(
                    game_id, team_id, game["time_for_guessing"]
                )
            
            await manager.broadcast_state(game_id, updated_game)
    else:
        # No need to broadcast on wrong guess, attempt counter is enough
        pass


@router.websocket("/player/{game_id}")
async def handle_player(websocket: WebSocket, game_id: str):
    """WebSocket endpoint for players participating in the game."""
    player_name = websocket.query_params.get("name")
    team_id = websocket.query_params.get("team_id")
    if not player_name or not team_id:
        await websocket.close(code=1008, reason="Missing player's name or team ID")
        return

    game = await games.find_one({"_id": game_id})
    if not game or team_id not in game["teams"]:
        await websocket.close(code=1011, reason="Game or team not found")
        return

    if game.get("game_state") != "pending":
        await websocket.close(code=1011, reason="Game is already in progress or finished")
        return

    await manager.connect_player(websocket, game_id, player_name, team_id)
    
    updated_game = await add_player_to_game(game_id, player_name, team_id)

    try:
        await manager.broadcast_state(game_id, updated_game)

        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            
            current_game = await games.find_one({"_id": game_id})
            if not current_game or current_game.get("game_state") == "finished":
                break

            if action == "switch_team" and current_game["game_state"] == "pending":
                team_id = await _handle_switch_team(
                    game_id, player_name, team_id, data, websocket
                )
            elif action == "skip" and current_game["teams"][team_id].get("current_master") == player_name:
                await _handle_skip_action(game_id, team_id, current_game["time_for_guessing"])
            elif action == "guess":
                await _handle_guess_action(game_id, player_name, team_id, data, current_game)

    except (WebSocketDisconnect, Exception) as e:
        print(f"Player {player_name} disconnected or error: {e}")
    finally:
        manager.disconnect(game_id, websocket)
        updated_game = await remove_player_from_game(game_id, player_name, team_id)
        await manager.broadcast_state(game_id, updated_game)