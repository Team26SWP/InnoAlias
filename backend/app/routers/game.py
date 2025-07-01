from asyncio import wait_for, TimeoutError
from datetime import datetime, timezone
from random import shuffle
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
    compute_team_scores, compute_team_scoreboard,
)

router = APIRouter(prefix="", tags=["game"])


@router.post("/create")
async def create_game(game: Game):
    words = game.remaining_words
    shuffle(words)

    amount = game.words_amount if game.words_amount is not None else len(words)

    code = await generate_game_code()
    new_game = {
        "_id": code,
        "remaining_words": words[:amount],
        "deck": words,
        "current_word": None,
        "expires_at": None,
        "tries_per_player": game.tries_per_player,
        "right_answers_to_advance": game.right_answers_to_advance,
        "current_correct": 0,
        "player_attempts": {},
        "correct_players": [],
        "time_for_guessing": game.time_for_guessing,
        "state": "pending",
        "rotate_masters": game.rotate_masters,
        "current_master": None,
        "team_count": game.team_count,
        "player_teams": {},
    }

    if game.team_count > 1:
        team_states = {}
        for i in range(1, game.team_count + 1):
            team_states[str(i)] = {
                "remaining_words": words[:amount],
                "current_word": None,
                "expires_at": None,
                "current_correct": 0,
                "player_attempts": {},
                "correct_players": [],
                "current_master": None,
                "state": "pending",
            }
        new_game["team_states"] = team_states

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
    host_name = websocket.query_params.get("name")
    if not await games.find_one({"_id": game_id}):
        await websocket.close(code=1011, reason="Game not found")
        return

    is_connected = await manager.connect_host(websocket, game_id, host_name)
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
                    if game.get("team_states"):
                        for t in list(game["team_states"].keys()):
                            await process_new_word(game_id, game["time_for_guessing"], t)
                        new_state = await games.find_one({"_id": game_id})
                    else:
                        new_state = await process_new_word(
                            game_id, game["time_for_guessing"]
                        )
                    await manager.broadcast_state(game_id, new_state)
                elif action == "skip" and game.get("state") == "in_progress":
                    print(f"Getting next word for {game_id}")
                    if game.get("team_states"):
                        for t in list(game["team_states"].keys()):
                            await process_new_word(game_id, game["time_for_guessing"], t)
                        new_state = await games.find_one({"_id": game_id})
                    else:
                        new_state = await process_new_word(
                            game_id, game["time_for_guessing"]
                        )
                    await manager.broadcast_state(game_id, new_state)

            except TimeoutError:
                if game.get("state") == "in_progress":
                    if game.get("team_states"):
                        for t in list(game["team_states"].keys()):
                            await process_new_word(game_id, game["time_for_guessing"], t)
                        new_state = await games.find_one({"_id": game_id})
                    else:
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
        manager.disconnect(game_id, websocket)


@router.get("/leaderboard/{game_id}")
async def get_leaderboard(game_id: str):
    if not await games.find_one({"_id": game_id}):
        raise HTTPException(status_code=404, detail="Game not found")

    game = await games.find_one({"_id": game_id})
    if game.get("player_teams"):
        return compute_team_scoreboard(game)

    scores = game.get("scores", {})
    return dict(sorted(scores.items(), key=lambda kv: kv[1], reverse=True))


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
    team = websocket.query_params.get("team", "1")
    if not player_name:
        await websocket.close(code=1008, reason="Missing player's name")
        return

    if not await games.find_one({"_id": game_id}):
        await websocket.close(code=1011, reason="Game not found")
        return

    await manager.connect_player(websocket, game_id, player_name, team)
    await games.update_one(
        {"_id": game_id, f"scores.{player_name}": {"$exists": False}},
        {"$set": {f"scores.{player_name}": 0}},
    )
    await games.update_one(
        {"_id": game_id},
        {
            "$set": {
                f"player_attempts.{player_name}": 0,
                f"player_teams.{player_name}": team,
            }
        },
    )
    try:

        game = await games.find_one({"_id": game_id})
        await manager.broadcast_state(game_id, game)

        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "skip":
                async with manager.locks[game_id]:
                    game = await games.find_one({"_id": game_id})
                    if (
                        game.get("rotate_masters")
                        and game.get("state") == "in_progress"
                        and player_name == game.get("team_states", {}).get(team, {}).get("current_master")
                    ):
                        new_state = await process_new_word(
                            game_id, game["time_for_guessing"], team
                        )
                        await manager.broadcast_state(game_id, new_state)
                continue

            if action == "switch_team":
                new_team = str(data.get("team", "1"))
                manager.switch_team(game_id, websocket, new_team)
                team = new_team

                await games.update_one(
                    {"_id": game_id},
                    {"$set": {f"player_teams.{player_name}": new_team}},
                )

                game = await games.find_one({"_id": game_id})
                await manager.broadcast_state(game_id, game)
                continue

            if action != "guess":
                continue

            guess = data.get("guess", "").strip().lower()

            async with manager.locks[game_id]:
                game = await games.find_one({"_id": game_id})
                if game["state"] != "in_progress":
                    continue

                team_state = game.get("team_states", {}).get(team, {})

                if game.get("rotate_masters") and player_name == team_state.get("current_master"):
                    continue

                if not game.get("rotate_masters") and player_name == manager.host_names.get(game_id):
                    continue

                tries_per_player = game.get("tries_per_player", 0)
                attempts = team_state.get("player_attempts", {}).get(player_name, 0)

                if player_name in team_state.get("correct_players", []):
                    continue

                if tries_per_player and attempts >= tries_per_player:
                    continue

                expires_at = team_state.get("expires_at")
                if expires_at and expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)

                if expires_at and datetime.now(timezone.utc) > expires_at:
                    continue

                if team_state.get("current_word") and guess == team_state["current_word"].lower():
                    update = {
                        "$set": {f"team_states.{team}.player_attempts.{player_name}": attempts + 1},
                    }

                    if player_name not in team_state.get("correct_players", []):
                        update.setdefault("$inc", {})[f"scores.{player_name}"] = 1
                        update["$inc"][f"team_states.{team}.current_correct"] = 1
                        update.setdefault("$addToSet", {})[f"team_states.{team}.correct_players"] = player_name

                    new_state = await games.find_one_and_update(
                        {"_id": game_id},
                        update,
                        return_document=ReturnDocument.AFTER,
                    )
                else:
                    await games.update_one(
                        {"_id": game_id},
                        {"$set": {f"team_states.{team}.player_attempts.{player_name}": attempts + 1}},
                    )
                    new_state = await games.find_one({"_id": game_id})

                team_state_after = new_state.get("team_states", {}).get(team, {})
                if team_state_after.get("current_correct", 0) >= required_to_advance(new_state, team):
                    new_state = await process_new_word(
                        game_id, game["time_for_guessing"], team
                    )

            team_state_after = new_state.get("team_states", {}).get(team, {})
            if team_state_after.get("current_correct", 0) < required_to_advance(new_state, team):
                tries_per_player = new_state.get("tries_per_player", 0)
                if tries_per_player:
                    attempts_map = team_state_after.get("player_attempts", {})
                    team_players = [p for p, t in new_state.get("player_teams", {}).items() if t == team]
                    all_spent = all(
                        attempts_map.get(p, 0) >= tries_per_player or p in team_state_after.get("correct_players", [])
                        for p in team_players
                    )
                    if all_spent:
                        new_state = await process_new_word(
                            game_id,
                            new_state.get("time_for_guessing", 0),
                            team,
                        )

            await manager.broadcast_state(game_id, new_state)

    except WebSocketDisconnect:
        name = manager.disconnect(game_id, websocket)
        if name:
            unset_fields = {
                f"scores.{name}": "",
                f"player_teams.{name}": "",
            }
            pull_fields = {"correct_players": name}
            for t in (game.get("team_states") or {}).keys():
                unset_fields[f"team_states.{t}.player_attempts.{name}"] = ""
                pull_fields[f"team_states.{t}.correct_players"] = name
            await games.update_one(
                {"_id": game_id, "state": "pending"},
                {
                    "$unset": unset_fields,
                    "$pull": pull_fields,
                },
            )
    except Exception as e:
        print(e)
        name = manager.disconnect(game_id, websocket)
        if name:
            unset_fields = {
                f"scores.{name}": "",
                f"player_teams.{name}": "",
            }
            pull_fields = {"correct_players": name}
            for t in (game.get("team_states") or {}).keys():
                unset_fields[f"team_states.{t}.player_attempts.{name}"] = ""
                pull_fields[f"team_states.{t}.correct_players"] = name
            await games.update_one(
                {"_id": game_id, "state": "pending"},
                {
                    "$unset": unset_fields,
                    "$pull": pull_fields,
                },
            )
