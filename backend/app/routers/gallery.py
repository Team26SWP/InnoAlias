from fastapi import APIRouter, HTTPException
from pymongo import DESCENDING
from fastapi import Depends
from backend.app.models import DeckIn, UserInDB, Deck
from backend.app.services.auth_service import get_current_user, users
from backend.app.services.game_service import decks

router = APIRouter(prefix="", tags=["gallery"])



@router.get("/decks")
async def get_gallery(number: int):
    if number < 1:
        raise HTTPException(status_code=404, detail="Invalid number")
    cursor = await decks.find({"private": False}).skip(number * 50 - 50).limit(50).sort("name", DESCENDING).to_list()
    return {
        "gallery": cursor,
        "total_decks": await decks.find({"private": False}).count(),
    }


@router.put("/decks/save/{deck_id}")
async def save_deck_from_gallery (
    deck_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    temp_user = await users.find_one({"_id": current_user.id}) if current_user else None
    temp_deck = await decks.find_one({"_id": deck_id}) if deck_id else None
    if not await temp_user:
        raise HTTPException(status_code=404, detail="User not found")
    if not await temp_deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    if current_user.id in await temp_deck.get("owner_ids"):
        raise HTTPException(status_code=404, detail="Already have this deck")
    if await temp_deck.get("private"):
        raise HTTPException(status_code=403, detail="Forbidden")
    await decks.update_one({"_id": deck_id}, {"$addToSet": {"owner_ids": current_user.id}})
    await users.update_one(
        {"_id": current_user.id}, {"$addToSet": {"deck_ids": deck_id}}
)
    return {"saved_deck_id": deck_id}