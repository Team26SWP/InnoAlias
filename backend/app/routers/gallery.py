from fastapi import APIRouter, HTTPException
from pymongo import DESCENDING
from fastapi import Depends

from backend.app.code_gen import generate_deck_id
from backend.app.models import UserInDB
from backend.app.services.auth_service import get_current_user, users
from backend.app.services.game_service import decks

router = APIRouter(prefix="", tags=["gallery"])


@router.get("/decks")
async def get_gallery(number: int):
    if number < 1:
        raise HTTPException(status_code=404, detail="Invalid number")
    cursor = (
        await decks.find({"private": False})
        .skip(number * 50 - 50)
        .limit(50)
        .sort("name", DESCENDING)
        .to_list()
    )
    return {
        "gallery": cursor,
        "total_decks": await decks.count_documents({"private": False})
    }


@router.put("/decks/{deck_id}")
async def save_deck_from_gallery(
    deck_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    temp_user = await users.find_one({"_id": current_user.id})
    temp_deck = await decks.find_one({"_id": deck_id})
    if not temp_user:
        raise HTTPException(status_code=404, detail="User not found")
    if not temp_deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    if current_user.id in await temp_deck.get("owner_ids"):
        raise HTTPException(status_code=404, detail="Already have this deck")
    if await temp_deck.get("private"):
        raise HTTPException(status_code=403, detail="Forbidden")
    new_deck_id = generate_deck_id()
    deck = {
        "_id": new_deck_id,
        "name": temp_deck["name"],
        "owner_id": temp_user.id,
        "words": temp_deck["words"],
        "tags": temp_deck["tags"],
        "private": temp_deck["private"],
    }
    await decks.insert_one(deck)
    await users.update_one(
        {"_id": current_user.id}, {"$addToSet": {"deck_ids": new_deck_id}}
    )
    return {"saved_deck_id": deck_id}
