from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.app.models import AIGame
from backend.app.services.aigame_service import (
    manager,
    create_aigame,
    start_aigame_service,
    handle_guess,
    skip_word,
    check_timer,
    aigames,
)
import asyncio

router = APIRouter(tags=["aigame"])


@router.post("/create")
async def create_ai_game_endpoint(game: AIGame):
    """
    Creates a new AI game.
    """
    game_id = await create_aigame(game)
    return {"game_id": game_id}


@router.websocket("/{game_id}")
async def aigame_websocket(websocket: WebSocket, game_id: str):
    """
    Handles WebSocket connections for AI game interactions.
    Manages game state updates, guesses, skips, and timer.
    """
    await manager.connect(websocket, game_id)
    timer_task = None

    try:
        game = await aigames.find_one({"_id": game_id})
        if game:
            await manager.send_state(game_id, game)
            if game.get("game_state") == "in_progress":
                timer_task = asyncio.create_task(check_timer(game_id))

        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "start_game":
                await start_aigame_service(game_id)
                if not timer_task or timer_task.done():
                    timer_task = asyncio.create_task(check_timer(game_id))

            elif action == "guess":
                guess = data.get("guess")
                await handle_guess(game_id, guess)

            elif action == "skip":
                await skip_word(game_id)

    except WebSocketDisconnect:
        manager.disconnect(game_id)
        if timer_task:
            timer_task.cancel()
