from fastapi import Depends, APIRouter, Query
from backend.app.models import UserInDB, ProfileResponse, DeckIn, DeckUpdate, DeckDetail
from backend.app.services.auth_service import get_current_user
from backend.app.services.profile_service import (
    get_profile_service,
    save_deck_service,
    edit_deck_service,
    get_deck_detail_service,
    delete_deck_service,
)

router = APIRouter(prefix="", tags=["profile"])

@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(
    search: str = Query(None), current_user: UserInDB = Depends(get_current_user)
):
    """
    Retrieves the profile of the current authenticated user.
    """
    return await get_profile_service(current_user.id, current_user, search)

@router.get("/{user_id}", response_model=ProfileResponse)
async def get_profile(
    user_id: str,
    current_user: UserInDB = Depends(get_current_user),
    search: str = Query(None),
):
    """
    Retrieves the profile of a specific user by ID. Requires the current user to be the owner of the profile.
    """
    return await get_profile_service(user_id, current_user, search)

@router.post("/deck/save")
async def save_deck_into_profile(
    deck: DeckIn,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Saves a new deck to the current user's profile.
    """
    return await save_deck_service(deck, current_user)

@router.patch("/deck/{deck_id}/edit", response_model=DeckDetail)
async def edit_deck(
    deck_id: str,
    deck: DeckUpdate,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Edits an existing deck in the current user's profile.
    """
    return await edit_deck_service(deck_id, deck, current_user)

@router.get("/deck/{deck_id}", response_model=DeckDetail)
async def get_additional_deck_info(deck_id: str):
    """
    Retrieves detailed information for a specific deck.
    """
    return await get_deck_detail_service(deck_id)

@router.delete("/deck/{deck_id}/delete")
async def delete_deck(deck_id: str, current_user: UserInDB = Depends(get_current_user)):
    """
    Deletes a deck from the current user's profile.
    """
    return await delete_deck_service(deck_id, current_user)

