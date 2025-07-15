from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pymongo import DESCENDING
from fastapi import Depends

from backend.app.code_gen import generate_deck_id
from backend.app.models import UserInDB
from backend.app.services.auth_service import get_current_user, users
from backend.app.services.game_service import decks

router = APIRouter(prefix="", tags=["gallery"])


@router.get("/decks")
async def get_gallery(number: int, search: str = Query(None, min_length=1)):
    if number < 1:
        raise HTTPException(status_code=404, detail="Invalid number")

    query: Dict[str, Any] = {"private": False}
    if search:
        query["$text"] = {"$search": search}

    cursor = decks.find(query).skip(number * 50 - 50).limit(50).sort("name", DESCENDING)

    gallery_decks = await cursor.to_list(length=50)
    total_decks = await decks.count_documents(query)

    return {
        "gallery": gallery_decks,
        "total_decks": total_decks,
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
    if current_user.id in temp_deck.get("owner_ids"):
        raise HTTPException(status_code=404, detail="Already have this deck")
    if temp_deck.get("private"):
        raise HTTPException(status_code=403, detail="Forbidden")
    new_deck_id = await generate_deck_id()
    deck = {
        "_id": new_deck_id,
        "name": temp_deck["name"],
        "owner_ids": [temp_user["_id"]],
        "words": temp_deck["words"],
        "tags": temp_deck["tags"],
        "private": temp_deck["private"],
    }
    await decks.insert_one(deck)
    await users.update_one(
        {"_id": current_user.id}, {"$addToSet": {"deck_ids": new_deck_id}}
    )
    return {"saved_deck_id": new_deck_id}
