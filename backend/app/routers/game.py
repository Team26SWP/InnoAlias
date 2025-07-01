from asyncio import wait_for, TimeoutError
from datetime import datetime, timezone
from random import shuffle, choice # Import choice
from fastapi.responses import Response
from pymongo import ReturnDocument
from fastapi import WebSocket, WebSocketDisconnect, APIRouter, HTTPException

from backend.app.code_gen import generate_game_code
from backend.app.models import Game
from backend.app.services.game_service import (
    games,
    manager,
    process_new_word,
    required_to_advance,
    reassign_master,
)

router = APIRouter(prefix="", tags=["game"])


@router.post("/create")
async def create_game(game: Game):
    words = game.deck # Use the full deck for distribution
    shuffle(words)

    code = await generate_game_code()
    
    teams_data = {}
    words_per_team = len(words) // game.number_of_teams
    
    for i in range(game.number_of_teams):
        team_id = f"team_{i+1}"
        team_name = f"Team {i+1}"
        
        start_index = i * words_per_team
        end_index = start_index + words_per_team
        
        # Distribute words, ensuring the last team gets any remainder
        team_words = words[start_index:end_index]
        if i == game.number_of_teams - 1:
            team_words = words[start_index:]

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

    print(f"DEBUG: Creating game with {game.number_of_teams} teams.")
    print(f"DEBUG: Teams data: {teams_data}")
    new_game = {
        "_id": code,
        "host_id": game.host_id,
        "number_of_teams": game.number_of_teams,
        "teams": teams_data, # This is where teams_data is assigned
        "deck": game.deck, # Store the original full deck
        "words_amount": game.words_amount,
        "time_for_guessing": game.time_for_guessing,
        "tries_per_player": game.tries_per_player,
        "right_answers_to_advance": game.right_answers_to_advance,
        "rotate_masters": game.rotate_masters,
        "game_state": "pending", # Overall game state
        "winning_team": None,
    }

    result = await games.insert_one(new_game)
    return {"id": str(result.inserted_id)}


@router.get("/leaderboard/{game_id}/export")
async def export_deck_txt(game_id: str):
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
    game = await games.find_one({"_id": game_id})
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    return {"words": game.get("deck", [])}


@router.websocket("/{game_id}")
async def handle_game(websocket: WebSocket, game_id: str):
    host_id = websocket.query_params.get("id") # Changed to id for host
    if not await games.find_one({"_id": game_id, "host_id": host_id}): # Verify host_id
        await websocket.close(code=1011, reason="Game not found or not authorized as host")
        return

    is_connected = await manager.connect_host(websocket, game_id, host_id) # Pass host_id
    if not is_connected:
        return

    try:
        game = await games.find_one({"_id": game_id})
        await manager.broadcast_state(game_id, game)

        while True:
            game = await games.find_one({"_id": game_id})
            if not game:
                break

            # Host logic for team-based game
            # The host doesn't participate in guessing, only manages the game flow.
            # They can start/skip words for specific teams.
            try:
                data = await websocket.receive_json()
                action = data.get("action")
                team_id = data.get("team_id") # Host must specify which team

                if not team_id:
                    print(f"Host action missing team_id for game {game_id}")
                    continue

                game = await games.find_one({"_id": game_id})
                if not game or game.get("game_state") == "finished" or team_id not in game["teams"]:
                    print(f"Game {game_id} or team {team_id} not found for host action")
                    continue

                team_state = game["teams"][team_id]

                if action == "start" and team_state.get("state") == "pending":
                    # Set overall game state to in_progress if it's the first team starting
                    if game["game_state"] == "pending":
                        await games.update_one(
                            {"_id": game_id},
                            {"$set": {"game_state": "in_progress"}}
                        )
                        game["game_state"] = "in_progress" # Update local game object

                        # Initialize words for all teams when the game officially starts
                        for tid, team_data in game["teams"].items():
                            # Only process if the team is still pending and has remaining words
                            if team_data.get("state") == "pending" and team_data.get("remaining_words"):
                                await process_new_word(game_id, tid, game["time_for_guessing"])
                        
                        # Re-fetch the game state after all teams have been processed
                        game = await games.find_one({"_id": game_id})
                        await manager.broadcast_state(game_id, game) # Broadcast the fully initialized state
                    else:
                        # If game is already in progress, just process the word for the specific team
                        async with manager.locks[game_id]:
                            new_game_state = await process_new_word(
                                game_id, team_id, game["time_for_guessing"]
                            )
                        await manager.broadcast_state(game_id, new_game_state)
                elif action == "skip" and team_state.get("state") == "in_progress":
                    print(f"Host skipping word for team {team_id} in game {game_id}")
                    async with manager.locks[game_id]:
                        new_game_state = await process_new_word(
                            game_id, team_id, game["time_for_guessing"]
                        )
                    await manager.broadcast_state(game_id, new_game_state)

            except TimeoutError:
                # Host websocket doesn't have a timeout for receiving messages
                pass
            except Exception as e:
                print(f"Error in handle_game for {game_id}: {e}")
                break # Break the loop on unexpected errors

        print(f"Game {game_id} finished or host disconnected")

    except WebSocketDisconnect:
        print(f"Disconnected from {game_id}")
    except Exception as e:
        print(e)
    finally:
        manager.disconnect(game_id, websocket)


@router.get("/leaderboard/{game_id}")
async def get_leaderboard(game_id: str):
    game = await games.find_one({"_id": game_id})
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # Calculate total scores for each team
    team_scores = {}
    for team_id, team_data in game.get("teams", {}).items():
        team_scores[team_data["name"]] = sum(team_data.get("scores", {}).values())

    # Sort teams by total score
    sorted_teams = dict(sorted(team_scores.items(), key=lambda kv: kv[1], reverse=True))

    # Prepare detailed leaderboard with player scores within teams
    detailed_leaderboard = {}
    for team_name, total_score in sorted_teams.items():
        team_id = next((tid for tid, tdata in game["teams"].items() if tdata["name"] == team_name), None)
        if team_id:
            team_data = game["teams"][team_id]
            detailed_leaderboard[team_name] = {
                "total_score": total_score,
                "players": dict(sorted(team_data.get("scores", {}).items(), key=lambda kv: kv[1], reverse=True))
            }
    return detailed_leaderboard


@router.delete("/delete/{game_id}")
async def delete_game(game_id: str):
    if not await games.find_one({"_id": game_id}):
        raise HTTPException(status_code=404, detail="Game not found")

    await games.delete_one({"_id": game_id})
    return {
        "status": "OK",
    }


@router.websocket("/player/{game_id}")
async def handle_player(websocket: WebSocket, game_id: str):
    player_name = websocket.query_params.get("name")
    team_id = websocket.query_params.get("team_id") # Get team_id from query params
    if not player_name or not team_id:
        await websocket.close(code=1008, reason="Missing player's name or team ID")
        return

    game = await games.find_one({"_id": game_id})
    if not game:
        await websocket.close(code=1011, reason="Game not found")
        return

    if team_id not in game["teams"]:
        await websocket.close(code=1011, reason="Team not found in this game")
        return

    # Connect player to the game and team
    await manager.connect_player(websocket, game_id, player_name, team_id)

    # Add player to the team in the database if not already there
    await games.update_one(
        {"_id": game_id, f"teams.{team_id}.players": {"$ne": player_name}},
        {"$addToSet": {f"teams.{team_id}.players": player_name}}
    )

    # Initialize player score and attempts for the specific team
    await games.update_one(
        {"_id": game_id, f"teams.{team_id}.scores.{player_name}": {"$exists": False}},
        {"$set": {f"teams.{team_id}.scores.{player_name}": 0}},
    )
    await games.update_one(
        {"_id": game_id, f"teams.{team_id}.player_attempts.{player_name}": {"$exists": False}},
        {"$set": {f"teams.{team_id}.player_attempts.{player_name}": 0}}
    )

    # Logic to set the first player in a team as game master if rotate_masters is false
    game = await games.find_one({"_id": game_id}) # Re-fetch game after updates
    team_state = game["teams"][team_id]

    if not game.get("rotate_masters") and team_state.get("current_master") is None:
        # Atomically set current_master for this team if it's still None
        updated_game = await games.find_one_and_update(
            {"_id": game_id, f"teams.{team_id}.current_master": None},
            {"$set": {f"teams.{team_id}.current_master": player_name}},
            return_document=ReturnDocument.AFTER,
        )
        if updated_game:
            game = updated_game # Use the updated game state for broadcasting
            team_state = game["teams"][team_id] # Update team_state reference

    try:
        await manager.broadcast_state(game_id, game)

        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "switch_team":
                new_team_id = data.get("new_team_id")
                if not new_team_id:
                    await websocket.send_json({"error": "Missing new_team_id"})
                    continue

                game = await games.find_one({"_id": game_id})
                if game["game_state"] != "pending":
                    await websocket.send_json({"error": "Cannot switch team once game has started"})
                    continue
                
                if new_team_id not in game["teams"]:
                    await websocket.send_json({"error": "New team not found"})
                    continue

                if new_team_id == team_id:
                    await websocket.send_json({"message": "Already in this team"})
                    continue

                old_team_id = team_id
                # Remove player from old team
                await games.update_one(
                    {"_id": game_id},
                    {"$pull": {f"teams.{old_team_id}.players": player_name}}
                )
                await games.update_one(
                    {"_id": game_id},
                    {"$unset": {
                        f"teams.{old_team_id}.scores.{player_name}": "",
                        f"teams.{old_team_id}.player_attempts.{player_name}": ""
                    }}
                )
                # If the player was the game master of the old team, reassign
                old_team_data = (await games.find_one({"_id": game_id}))["teams"][old_team_id]
                if old_team_data.get("current_master") == player_name:
                    await reassign_master(game_id, old_team_id)

                # Add player to new team
                await games.update_one(
                    {"_id": game_id},
                    {"$addToSet": {f"teams.{new_team_id}.players": player_name}}
                )
                await games.update_one(
                    {"_id": game_id, f"teams.{new_team_id}.scores.{player_name}": {"$exists": False}},
                    {"$set": {f"teams.{new_team_id}.scores.{player_name}": 0}},
                )
                await games.update_one(
                    {"_id": game_id, f"teams.{new_team_id}.player_attempts.{player_name}": {"$exists": False}},
                    {"$set": {f"teams.{new_team_id}.player_attempts.{player_name}": 0}}
                )

                # Update player's team_id in manager
                manager.disconnect(game_id, websocket) # Disconnect old entry
                await manager.connect_player(websocket, game_id, player_name, new_team_id) # Connect with new team_id
                team_id = new_team_id # Update local team_id for subsequent actions

                # Re-evaluate game master for the new team if in single game master mode
                game = await games.find_one({"_id": game_id})
                new_team_state = game["teams"][new_team_id]
                if not game.get("rotate_masters") and new_team_state.get("current_master") is None:
                    await games.find_one_and_update(
                        {"_id": game_id, f"teams.{new_team_id}.current_master": None},
                        {"$set": {f"teams.{new_team_id}.current_master": player_name}},
                        return_document=ReturnDocument.AFTER,
                    )
                
                await manager.broadcast_state(game_id, game)
                continue

            if action == "skip":
                async with manager.locks[game_id]:
                    game = await games.find_one({"_id": game_id})
                    if not game or game.get("game_state") == "finished":
                        continue
                    team_state = game["teams"].get(team_id)
                    if not team_state:
                        continue

                    if (
                        team_state.get("state") == "in_progress"
                        and player_name == team_state.get("current_master")
                    ):
                        new_state = await process_new_word(
                            game_id, team_id, game["time_for_guessing"]
                        )
                        await manager.broadcast_state(game_id, new_state)
                continue

            if action != "guess":
                continue

            guess = data.get("guess", "").strip().lower()

            async with manager.locks[game_id]:
                game = await games.find_one({"_id": game_id})
                if not game or game.get("game_state") == "finished":
                    continue
                team_state = game["teams"].get(team_id)
                if not team_state or team_state["state"] != "in_progress":
                    continue

                # Player is game master, cannot guess
                if player_name == team_state.get("current_master"):
                    continue

                # Check if player already guessed correctly for this word
                if player_name in team_state.get("correct_players", []):
                    continue

                tries_per_player = game.get("tries_per_player", 0) # From game level
                attempts = team_state.get("player_attempts", {}).get(player_name, 0)

                if tries_per_player and attempts >= tries_per_player:
                    continue

                expires_at = team_state.get("expires_at")
                if expires_at and expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)

                if expires_at and datetime.now(timezone.utc) > expires_at:
                    continue

                if guess == team_state["current_word"].lower():
                    update_fields = {
                        f"teams.{team_id}.player_attempts.{player_name}": attempts + 1,
                    }

                    if player_name not in team_state.get("correct_players", []):
                        update_fields[f"teams.{team_id}.scores.{player_name}"] = team_state.get("scores", {}).get(player_name, 0) + 1
                        update_fields[f"teams.{team_id}.current_correct"] = team_state.get("current_correct", 0) + 1
                        update_fields["$addToSet"] = {f"teams.{team_id}.correct_players": player_name}
                    
                    # Use $set for direct updates, $addToSet for array
                    update_operation = {"$set": {k: v for k, v in update_fields.items() if k != "$addToSet"}}
                    if "$addToSet" in update_fields:
                        update_operation["$addToSet"] = update_fields["$addToSet"]

                    new_game_state = await games.find_one_and_update(
                        {"_id": game_id},
                        update_operation,
                        return_document=ReturnDocument.AFTER,
                    )
                else:
                    new_game_state = await games.find_one_and_update(
                        {"_id": game_id},
                        {"$set": {f"teams.{team_id}.player_attempts.{player_name}": attempts + 1}},
                        return_document=ReturnDocument.AFTER,
                    )
                
                # Re-fetch team_state from the updated game state
                team_state = new_game_state["teams"][team_id]

                if team_state.get("current_correct", 0) >= required_to_advance(
                    team_state
                ):
                    new_game_state = await process_new_word(
                        game_id, team_id, game["time_for_guessing"]
                    )
            
            # Re-fetch team_state from the updated game state if process_new_word was called
            team_state = new_game_state["teams"][team_id]

            if team_state.get("current_correct", 0) < required_to_advance(team_state):
                tries_per_player = game.get("tries_per_player", 0) # From game level
                if tries_per_player:
                    attempts_map = team_state.get("player_attempts", {})
                    players_in_team = team_state.get("players", [])
                    
                    # Filter out the current master from players to check attempts
                    players_to_check = [p for p in players_in_team if p != team_state.get("current_master")]

                    all_spent = all(
                        attempts_map.get(p, 0) >= tries_per_player
                        or p in team_state.get("correct_players", [])
                        for p in players_to_check
                    )
                    if all_spent:
                        new_game_state = await process_new_word(
                            game_id,
                            team_id,
                            game.get("time_for_guessing", 0),
                        )

            await manager.broadcast_state(game_id, new_game_state)

    except WebSocketDisconnect:
        name = manager.disconnect(game_id, websocket)
        if name:
            # Remove player from their team in the database
            game = await games.find_one({"_id": game_id})
            if game and team_id in game["teams"]:
                await games.update_one(
                    {"_id": game_id},
                    {"$pull": {f"teams.{team_id}.players": name}}
                )
                await games.update_one(
                    {"_id": game_id},
                    {"$unset": {
                        f"teams.{team_id}.scores.{name}": "",
                        f"teams.{team_id}.player_attempts.{name}": ""
                    }}
                )
                # If the disconnected player was the game master, assign new one
                team_data_after_pull = (await games.find_one({"_id": game_id}))["teams"][team_id]
                if team_data_after_pull.get("current_master") == name:
                    await reassign_master(game_id, team_id)
    except Exception as e:
        print(e)
        name = manager.disconnect(game_id, websocket)
        if name:
            # Remove player from their team in the database on error
            game = await games.find_one({"_id": game_id})
            if game and team_id in game["teams"]:
                await games.update_one(
                    {"_id": game_id},
                    {"$pull": {f"teams.{team_id}.players": name}}
                )
                await games.update_one(
                    {"_id": game_id},
                    {"$unset": {
                        f"teams.{team_id}.scores.{name}": "",
                        f"teams.{team_id}.player_attempts.{name}": ""
                    }}
                )
                # If the disconnected player was the game master, assign new one
                team_data_after_pull = (await games.find_one({"_id": game_id}))["teams"][team_id]
                if team_data_after_pull.get("current_master") == name:
                    await reassign_master(game_id, team_id)
