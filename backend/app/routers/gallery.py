from fastapi import APIRouter, Depends, Query

from backend.app.models import UserInDB
from backend.app.services.auth_service import get_current_user
from backend.app.services.gallery_service import (
    get_gallery_service,
    save_deck_from_gallery_service,
)

router = APIRouter(prefix="", tags=["gallery"])


@router.get("/decks")
async def get_gallery(number: int, search: str = Query(None, min_length=1)):
    """
    Retrieves a paginated list of public decks from the gallery.
    """
    return await get_gallery_service(number, search)


@router.put("/decks/{deck_id}")
async def save_deck_from_gallery(
    deck_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Saves a deck from the gallery to the current user's profile.
    """
    return await save_deck_from_gallery_service(deck_id, current_user)
