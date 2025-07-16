from fastapi import HTTPException
from pymongo import DESCENDING
from typing import Any, Dict

from backend.app.code_gen import generate_deck_id
from backend.app.db import db
from backend.app.models import (
    UserInDB,
    ProfileResponse,
    DeckPreview,
    DeckIn,
    DeckUpdate,
    DeckDetail,
)

users = db.users
decks = db.decks

async def get_profile_service(
    user_id: str,
    current_user: UserInDB,
    search: str | None = None,
):
    """
    Retrieves a user's profile and their associated decks.
    Requires the current user to be the owner of the profile.
    """
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    user_data = await users.find_one({"_id": user_id})
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    deck_ids = user_data.get("deck_ids", [])
    user_decks = []

    if deck_ids:
        query: Dict[str, Any] = {"_id": {"$in": deck_ids}}
        if search:
            query["$text"] = {"$search": search}

        cursor = decks.find(query, {"name": 1, "words": 1, "tags": 1}).sort(
            "name", DESCENDING
        )

        user_decks = await cursor.to_list(length=100)

    return ProfileResponse(
        id=user_data["_id"],
        name=user_data["name"],
        surname=user_data["surname"],
        email=user_data["email"],
        isAdmin=user_data.get("isAdmin", False),
        decks=[
            DeckPreview(
                id=deck["_id"],
                name=deck["name"],
                words_count=len(deck.get("words", [])),
                tags=deck.get("tags"),
            )
            for deck in user_decks
        ],
    )

async def save_deck_service(
    deck: DeckIn,
    current_user: UserInDB,
):
    """
    Saves a new deck to the current user's profile.
    """
    if not await users.find_one({"_id": current_user.id}):
        raise HTTPException(status_code=404, detail="User not found")
    deck_id = await generate_deck_id()
    temp_deck = {
        "_id": deck_id,
        "name": deck.deck_name,
        "tags": deck.tags,
        "words": deck.words,
        "owner_ids": [current_user.id],
        "private": False,
    }

    await decks.insert_one(temp_deck)
    await users.update_one(
        {"_id": current_user.id}, {"$addToSet": {"deck_ids": deck_id}}
    )
    return {"inserted_id": deck_id}

async def edit_deck_service(
    deck_id: str,
    deck_update: DeckUpdate,
    current_user: UserInDB,
):
    """
    Edits an existing deck in the current user's profile.
    Ensures the deck exists and the current user is an owner.
    """
    existing = await decks.find_one({"_id": deck_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Deck not found")
    if current_user.id not in existing.get("owner_ids", []):
        raise HTTPException(status_code=403, detail="Forbidden")

    update_data: dict[str, Any] = {}
    if deck_update.deck_name is not None:
        update_data["name"] = deck_update.deck_name
    if deck_update.words is not None:
        update_data["words"] = deck_update.words
    if deck_update.tags is not None:
        update_data["tags"] = deck_update.tags
    if deck_update.private is not None:
        update_data["private"] = deck_update.private

    if update_data:
        await decks.update_one({"_id": deck_id}, {"$set": update_data})

    updated = await decks.find_one({"_id": deck_id})
    if not isinstance(updated, dict):
        raise HTTPException(status_code=404, detail="Deck not found")
    return DeckDetail(
        id=updated["_id"],
        name=updated["name"],
        words_count=len(updated.get("words", [])),
        tags=updated.get("tags"),
        words=updated.get("words", []),
        private=updated.get("private", False),
    )

async def get_deck_detail_service(deck_id: str):
    """
    Retrieves detailed information for a specific deck.
    """
    deck = await decks.find_one({"_id": deck_id})
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    return DeckDetail(
        id=deck["_id"],
        name=deck["name"],
        words_count=len(deck.get("words", [])),
        tags=deck.get("tags"),
        words=deck.get("words", []),
    )

async def delete_deck_service(
    deck_id: str,
    current_user: UserInDB,
):
    """
    Deletes a deck from the current user's profile.
    If the deck has no other owners, it is completely removed from the database.
    """
    deck = await decks.find_one({"_id": deck_id})
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    if current_user.id not in deck.get("owner_ids", []):
        raise HTTPException(status_code=403, detail="Forbidden")

    await users.update_one(
        {"_id": current_user.id}, {"$pull": {"deck_ids": deck_id}}
    )
    await decks.update_one(
        {"_id": deck_id}, {"$pull": {"owner_ids": current_user.id}}
    )
    updated_deck = await decks.find_one({"_id": deck_id})
    if not updated_deck or not updated_deck.get("owner_ids"):
        await decks.delete_one({"_id": deck_id})
    return {"status": "deleted"}
