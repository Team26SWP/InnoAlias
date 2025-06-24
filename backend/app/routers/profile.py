from typing import List, Optional

from fastapi import HTTPException, Depends, APIRouter
from pydantic import BaseModel, Field
from pymongo import DESCENDING

from InnoAlias.backend.app.db import db
from InnoAlias.backend.app.models import UserInDB, ProfileResponse, DeckPreview
from InnoAlias.backend.app.routers.auth import get_current_user
from InnoAlias.backend.app.models import DeckDetail
router = APIRouter(prefix="", tags=["profile"])


@router.get("/{user_id}", response_model=ProfileResponse)
async def get_profile(
        user_id: str,
        current_user: UserInDB = Depends(get_current_user)
):
    if user_id != current_user.id:
        raise HTTPException(403, "Forbidden")

    user_data = await db.users.find_one({"_id": user_id})
    if not user_data:
        raise HTTPException(404, "User not found")
    deck_ids = user_data.get("deck_ids", [])
    decks = []

    if deck_ids:
        cursor = db.decks.find(
            {"_id": {"$in": deck_ids}},
            {"name": 1, "words": 1, "tag": 1}
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
                tag=deck.get("tag")
            )
            for deck in decks
        ]
    )

@router.get("/{user_id}/decks/{deck_id}", response_model=DeckDetail)
async def get_additional_deck_info(
        deck_id: str,
        current_user: UserInDB = Depends(get_current_user)
):
    deck = await db.decks.find_one({"_id": deck_id})
    if not deck:
        raise HTTPException(404, "Deck not found")

    return DeckDetail(
        id=deck["_id"],
        name=deck["name"],
        words_count=len(deck.get("words", [])),
        tag=deck.get("tag"),
        words=deck.get("words", []),
    )


@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(current_user: UserInDB = Depends(get_current_user)):
    return await get_profile(current_user.id, current_user)