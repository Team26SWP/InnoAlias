from fastapi import HTTPException, Depends, APIRouter
from pymongo import DESCENDING
from typing import Any

from backend.app.code_gen import generate_deck_id
from backend.app.db import db
from backend.app.models import (
    UserInDB,
    ProfileResponse,
    DeckPreview,
    DeckIn,
    DeckUpdate,
)
from backend.app.services.auth_service import get_current_user
from backend.app.models import DeckDetail

router = APIRouter(prefix="", tags=["profile"])


@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(current_user: UserInDB = Depends(get_current_user)):
    return await get_profile(current_user.id, current_user)


@router.get("/{user_id}", response_model=ProfileResponse)
async def get_profile(user_id: str, current_user: UserInDB = Depends(get_current_user)):
    if user_id != current_user.id:
        raise HTTPException(403, "Forbidden")

    user_data = await db.users.find_one({"_id": user_id})
    if not user_data:
        raise HTTPException(404, "User not found")

    deck_ids = user_data.get("deck_ids", [])
    decks = []

    if deck_ids:
        cursor = db.decks.find(
            {"_id": {"$in": deck_ids}}, {"name": 1, "words": 1, "tags": 1}
        ).sort("name", DESCENDING)

        decks = await cursor.to_list(length=100)

    return ProfileResponse(
        id=user_data["_id"],
        name=user_data["name"],
        surname=user_data["surname"],
        email=user_data["email"],
        decks=[
            DeckPreview(
                id=deck["_id"],
                name=deck["name"],
                words_count=len(deck.get("words", [])),
                tags=deck.get("tags"),
            )
            for deck in decks
        ],
    )


@router.post("/deck/save")
async def save_deck_into_profile(
    deck: DeckIn,
    current_user: UserInDB = Depends(get_current_user),
):
    temp_cursor = db.decks.find({"name": deck.name})
    if temp_cursor:
        raise HTTPException(400, "Deck with this name already exists")
    if not await db.users.find_one({"_id": current_user.id}):
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

    await db.decks.insert_one(temp_deck)
    await db.users.update_one(
        {"_id": current_user.id}, {"$addToSet": {"deck_ids": deck_id}}
    )
    return {"inserted_id": deck_id}


@router.patch("/deck/{deck_id}/edit", response_model=DeckDetail)
async def edit_deck(
    deck_id: str,
    deck: DeckUpdate,
    current_user: UserInDB = Depends(get_current_user),
):
    existing = await db.decks.find_one({"_id": deck_id})
    if not existing:
        raise HTTPException(404, "Deck not found")
    if current_user.id not in existing.get("owner_ids", []):
        raise HTTPException(403, "Forbidden")

    update_data: dict[str, Any] = {}
    if deck.deck_name is not None:
        update_data["name"] = deck.deck_name
    if deck.words is not None:
        update_data["words"] = deck.words
    if deck.tags is not None:
        update_data["tags"] = deck.tags
    if deck.private is not None:
        update_data["private"] = deck.private

    if update_data:
        await db.decks.update_one({"_id": deck_id}, {"$set": update_data})

    updated = await db.decks.find_one({"_id": deck_id})
    if not isinstance(updated, dict):
        raise HTTPException(404, "Deck not found")
    return DeckDetail(
        id=updated["_id"],
        name=updated["name"],
        words_count=len(updated.get("words", [])),
        tags=updated.get("tags"),
        words=updated.get("words", []),
        private=updated.get("private", False),
    )


@router.get("/deck/{deck_id}", response_model=DeckDetail)
async def get_additional_deck_info(deck_id: str):
    deck = await db.decks.find_one({"_id": deck_id})
    if not deck:
        raise HTTPException(404, "Deck not found")

    return DeckDetail(
        id=deck["_id"],
        name=deck["name"],
        words_count=len(deck.get("words", [])),
        tags=deck.get("tags"),
        words=deck.get("words", []),
    )


@router.delete("/deck/{deck_id}/delete")
async def delete_deck(deck_id: str, current_user: UserInDB = Depends(get_current_user)):
    deck = await db.decks.find_one({"_id": deck_id})
    if not deck:
        raise HTTPException(404, "Deck not found")
    if current_user.id not in deck.get("owner_ids", []):
        raise HTTPException(403, "Forbidden")

    await db.users.update_one(
        {"_id": current_user.id}, {"$pull": {"deck_ids": deck_id}}
    )
    await db.decks.update_one(
        {"_id": deck_id}, {"$pull": {"owner_ids": current_user.id}}
    )
    updated_deck = await db.decks.find_one({"_id": deck_id})
    if not updated_deck or not updated_deck.get("owner_ids"):
        await db.decks.delete_one({"_id": deck_id})
    return {"status": "deleted"}
