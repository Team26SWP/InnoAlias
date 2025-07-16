from typing import Dict, Any
from fastapi import HTTPException, status
from pymongo import DESCENDING

from backend.app.code_gen import generate_deck_id
from backend.app.models import UserInDB
from backend.app.services.auth_service import users
from backend.app.services.game_service import decks
from backend.app.config import GALLERY_PAGE_SIZE


async def get_gallery_service(number: int, search: str | None = None):
    """
    Retrieves a paginated list of public decks from the gallery based on the page number and an optional search query.
    """
    if number < 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid number"
        )

    query: Dict[str, Any] = {"private": False}
    if search:
        query["$text"] = {"$search": search}

    cursor = (
        decks.find(query)
        .skip(number * GALLERY_PAGE_SIZE - GALLERY_PAGE_SIZE)
        .limit(GALLERY_PAGE_SIZE)
        .sort("name", DESCENDING)
    )

    gallery_decks = await cursor.to_list(length=GALLERY_PAGE_SIZE)
    total_decks = await decks.count_documents(query)

    return {
        "gallery": gallery_decks,
        "total_decks": total_decks,
    }


async def save_deck_from_gallery_service(
    deck_id: str,
    current_user: UserInDB,
):
    """
    Saves a deck from the gallery to the current user's profile.
    Ensures the user exists, the deck exists and is not private, and the user doesn't already own the deck.
    """
    user_doc = await users.find_one({"_id": current_user.id})
    gallery_deck_doc = await decks.find_one({"_id": deck_id})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if not gallery_deck_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found"
        )
    if current_user.id in gallery_deck_doc.get("owner_ids", []):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Already have this deck"
        )
    if gallery_deck_doc.get("private"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    new_deck_id = await generate_deck_id()
    deck = {
        "_id": new_deck_id,
        "name": gallery_deck_doc["name"],
        "owner_ids": [user_doc["_id"]],
        "words": gallery_deck_doc["words"],
        "tags": gallery_deck_doc["tags"],
        "private": gallery_deck_doc["private"],
    }
    await decks.insert_one(deck)
    await users.update_one(
        {"_id": current_user.id}, {"$addToSet": {"deck_ids": new_deck_id}}
    )
    return {"saved_deck_id": new_deck_id}
