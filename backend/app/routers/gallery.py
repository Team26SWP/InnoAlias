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
    deck: Deck,
    current_user: UserInDB = Depends(get_current_user),
):
    if not await users.find_one({"_id": current_user.id}):
        raise HTTPException(status_code=404, detail="User not found")
    if not await decks.find_one({"_id": deck.id}):
        raise HTTPException(status_code=404, detail="Deck not found")
    if current_user.id in await decks.find_one({"_id": deck.id}).get("owner_ids"):
        raise HTTPException(status_code=404, detail="Already have this deck")
    if await decks.find_one({"_id": deck.id}).get("private"):
        raise HTTPException(status_code=403, detail="Forbidden")
    await decks.update_one({"_id": deck.id}, {"$addToSet": {"owner_ids": current_user.id}})
    await users.update_one(
        {"_id": current_user.id}, {"$addToSet": {"deck_ids": deck.id}}
)
    return {"saved_deck_id": deck.id}