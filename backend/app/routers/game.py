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
    compute_team_scores,
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
        manager.disconnect(game_id, websocket)


@router.get("/leaderboard/{game_id}")
async def get_leaderboard(game_id: str):
    if not await games.find_one({"_id": game_id}):
        raise HTTPException(status_code=404, detail="Game not found")

    game = await games.find_one({"_id": game_id})
    team_scores = compute_team_scores(game)

    return dict(sorted(team_scores.items(), key=lambda kv: kv[1], reverse=True))


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
                        and player_name == game.get("current_master")
                    ):
                        new_state = await process_new_word(
                            game_id, game["time_for_guessing"]
                        )
                        await manager.broadcast_state(game_id, new_state)
                continue

            if action == "switch_team":
                new_team = str(data.get("team", "1"))
                manager.switch_team(game_id, websocket, new_team)

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

                if game.get("rotate_masters") and player_name == game.get(
                    "current_master"
                ):
                    continue

                if not game.get(
                    "rotate_masters"
                ) and player_name == manager.host_names.get(game_id):
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
                else:
                    await games.update_one(
                        {"_id": game_id},
                        {"$set": {f"player_attempts.{player_name}": attempts + 1}},
                    )
                    new_state = await games.find_one({"_id": game_id})

                if new_state.get("current_correct", 0) >= required_to_advance(
                    new_state
                ):
                    new_state = await process_new_word(
                        game_id, game["time_for_guessing"]
                    )

            if new_state.get("current_correct", 0) < required_to_advance(new_state):
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
        name = manager.disconnect(game_id, websocket)
        if name:
            await games.update_one(
                {"_id": game_id, "state": "pending"},
                {
                    "$unset": {
                        f"scores.{name}": "",
                        f"player_attempts.{name}": "",
                        f"player_teams.{name}": "",
                    },
                    "$pull": {"correct_players": name},
                },
            )
    except Exception as e:
        print(e)
        name = manager.disconnect(game_id, websocket)
        if name:
            await games.update_one(
                {"_id": game_id, "state": "pending"},
                {
                    "$unset": {
                        f"scores.{name}": "",
                        f"player_attempts.{name}": "",
                        f"player_teams.{name}": "",
                    },
                    "$pull": {"correct_players": name},
                },
            )
