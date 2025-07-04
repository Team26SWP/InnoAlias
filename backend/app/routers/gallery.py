from fastapi import WebSocket, WebSocketDisconnect, APIRouter, HTTPException
from pymongo import DESCENDING

from backend.app.services.game_service import decks

router = APIRouter(prefix="", tags=["gallery"])



@router.get("/decks")
async def get_gallery(number: int):
    cursor = await decks.find({"private": False}).skip(number * 50 - 50).limit(50).sort("name", DESCENDING).to_list()
    return {
        "gallery": cursor,
        "total_decks": cursor.count(),
    }

