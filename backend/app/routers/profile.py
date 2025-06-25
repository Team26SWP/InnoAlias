from fastapi import HTTPException, Depends, APIRouter
from pymongo import DESCENDING

from backend.app.db import db
from backend.app.models import UserInDB, ProfileResponse, DeckPreview
from backend.app.services.auth_service import get_current_user
from backend.app.models import DeckDetail

router = APIRouter(prefix="", tags=["profile"])


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
        cursor = await db.decks.find(
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


@router.delete("/deck/delete/{deck_id}")
async def delete_deck(deck_id: str, current_user: UserInDB = Depends(get_current_user)):
    deck = await db.decks.find_one({"_id": deck_id})
    if not deck:
        raise HTTPException(404, "Deck not found")
    if current_user.id not in deck.get("owner_ids", []):
        raise HTTPException(403, "Forbidden")

    await db.users.update_one({"_id": current_user.id}, {"$pull": {"deck_ids": deck_id}})
    await db.decks.update_one({"_id": deck_id}, {"$pull": {"owner_ids": current_user.id}})
    updated_deck = await db.decks.find_one({"_id": deck_id})
    if not updated_deck or not updated_deck.get("owner_ids"):
        await db.decks.delete_one({"_id": deck_id})
    return {"status": "deleted"}


@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(current_user: UserInDB = Depends(get_current_user)):
    return await get_profile(current_user.id, current_user)
