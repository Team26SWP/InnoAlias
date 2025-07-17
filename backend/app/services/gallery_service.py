from typing import Any

from fastapi import HTTPException, status
from pymongo import DESCENDING

from backend.app.code_gen import generate_deck_id
from backend.app.config import GALLERY_PAGE_SIZE
from backend.app.models import Deck, UserInDB
from backend.app.services.auth_service import users
from backend.app.services.game_service import decks


async def get_gallery_service(page: int, search: str | None = None):
    """
    Retrieves a paginated list of public decks from the gallery based on the page number and an optional search query.
    """
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page number must be 1 or greater",
        )

    query: dict[str, Any] = {"private": False}
    if search:
        query["$text"] = {"$search": search}

    skip_amount = (page - 1) * GALLERY_PAGE_SIZE

    pipeline = [
        {"$match": query},
        {"$sort": {"name": DESCENDING}},
        {
            "$facet": {
                "decks": [{"$skip": skip_amount}, {"$limit": GALLERY_PAGE_SIZE}],
                "total_count": [{"$count": "count"}],
            }
        },
    ]

    cursor = decks.aggregate(pipeline)
    result = await cursor.to_list(1)

    if not result:
        gallery_decks = []
        total_decks = 0
    else:
        gallery_decks = result[0]["decks"]
        total_decks = (
            result[0]["total_count"][0]["count"] if result[0]["total_count"] else 0
        )

    return {
        "gallery": [Deck(**deck) for deck in gallery_decks],
        "total_decks": total_decks,
    }


async def save_deck_from_gallery_service(
    deck_id: str,
    current_user: UserInDB,
):
    """
    Saves a deck from the gallery to the current user's profile.
    Ensures the deck exists and is not private, and the user doesn't already own the deck.
    """
    gallery_deck_doc = await decks.find_one({"_id": deck_id})

    if not gallery_deck_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found"
        )
    if current_user.id in gallery_deck_doc.get("owner_ids", []):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have this deck in your library",
        )
    if gallery_deck_doc.get("private"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This deck is private and cannot be saved",
        )

    new_deck_id = await generate_deck_id()
    deck_data = {
        "_id": new_deck_id,
        "name": gallery_deck_doc["name"],
        "owner_ids": [current_user.id],
        "words": gallery_deck_doc["words"],
        "tags": gallery_deck_doc["tags"],
        "private": gallery_deck_doc["private"],
    }

    new_deck = Deck(**deck_data)
    await decks.insert_one(new_deck.model_dump(by_alias=True))

    await users.update_one(
        {"_id": current_user.id}, {"$addToSet": {"deck_ids": new_deck_id}}
    )

    return {"saved_deck_id": new_deck_id}
