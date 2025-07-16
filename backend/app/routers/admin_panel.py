from fastapi import HTTPException, Depends, APIRouter
from backend.app.services.auth_service import get_current_user
from backend.app.services.admin_service import (
    delete_user_service,
    get_logs_service,
    delete_deck_service,
    add_admin_service,
    remove_admin_service,
    delete_tag_service,
    clear_logs_service,
)

router = APIRouter(prefix="", tags=["admin"])


async def admin_required(current_user=Depends(get_current_user)):
    """
    Dependency to ensure the current user is an administrator.
    Raises HTTPException 403 if the user is not an admin.
    """
    if not current_user.isAdmin:
        raise HTTPException(status_code=403, detail="Forbidden")
    return current_user


@router.delete("/delete/user/{email}")
async def delete_user(
    email: str,
    reason: str,
    current_user=Depends(admin_required),
):
    """
    Deletes a user by email. Requires administrator privileges.
    """
    return await delete_user_service(email, reason, current_user.email)


@router.get("/logs")
async def get_logs(current_user=Depends(admin_required)):
    """
    Retrieves all admin logs. Requires administrator privileges.
    """
    return await get_logs_service()


@router.delete("/delete/deck/{deck_id}")
async def delete_deck(deck_id: str, reason: str, current_user=Depends(admin_required)):
    """
    Deletes a deck by its ID. Requires administrator privileges.
    """
    return await delete_deck_service(deck_id, reason, current_user.email)


@router.put("/add/{email}")
async def add_admin(
    email: str,
    current_user=Depends(admin_required),
):
    """
    Grants administrator privileges to a user by email.
    Requires administrator privileges.
    """
    return await add_admin_service(email, current_user.email)


@router.put("/remove/{email}")
async def remove_admin(
    email: str,
    current_user=Depends(admin_required),
):
    """
    Revokes administrator privileges from a user by email.
    Requires administrator privileges.
    """
    return await remove_admin_service(email, current_user.email)


@router.delete("/delete/tag/{tag}")
async def delete_tag(
    tag: str,
    reason: str,
    current_user=Depends(admin_required),
):
    """
    Deletes a tag from all decks. Requires administrator privileges.
    """
    return await delete_tag_service(tag, reason, current_user.email)


@router.delete("/clear/logs")
async def clear_logs(current_user=Depends(admin_required)):
    """
    Clears all admin logs. Requires administrator privileges.
    """
    return await clear_logs_service(current_user.email)
