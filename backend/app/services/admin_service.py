from datetime import UTC, datetime

from fastapi import HTTPException

from backend.app.config import DEFAULT_REASON_MESSAGE
from backend.app.db import db
from backend.app.services.auth_service import users
from backend.app.services.game_service import decks

logs = db.logs


async def _log_admin_action(action: str, admin_email: str, **kwargs):
    """
    Logs an administrative action to the database.
    """
    log_entry = {
        "action": action,
        "admin_email": admin_email,
        "timestamp": datetime.now(UTC).isoformat(),
        **kwargs,
    }
    await logs.insert_one(log_entry)


async def delete_user_service(email: str, reason: str, admin_email: str):
    """
    Deletes a user and associated decks from the database.
    Logs the action.
    """
    user = await users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await users.delete_one({"email": email})
    await decks.update_many(
        {"owner_ids": user["_id"]}, {"$pull": {"owner_ids": user["_id"]}}
    )

    await _log_admin_action(
        action="DELETE_USER",
        admin_email=admin_email,
        target_user_id=user["_id"],
        target_user_email=email,
        reason=reason or DEFAULT_REASON_MESSAGE,
    )
    return {
        "message": f"User {email} deleted. Reason: {reason or DEFAULT_REASON_MESSAGE}."
    }


async def get_logs_service():
    """
    Retrieves all administrative logs.
    """
    show_logs = await logs.find().to_list(length=None)
    if not show_logs:
        raise HTTPException(status_code=404, detail="No logs")
    response_logs = [{**log, "_id": str(log["_id"])} for log in show_logs]
    return {"logs": response_logs}


async def delete_deck_service(deck_id: str, reason: str, admin_email: str):
    """
    Deletes a deck by its ID and removes it from all user profiles.
    Logs the action.
    """
    deck = await decks.find_one({"_id": deck_id})
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    await decks.delete_one({"_id": deck_id})
    await users.update_many({"deck_ids": deck_id}, {"$pull": {"deck_ids": deck_id}})

    await _log_admin_action(
        action="DELETE_DECK",
        admin_email=admin_email,
        target_deck_id=deck_id,
        reason=reason or DEFAULT_REASON_MESSAGE,
    )
    return {"message": f"{deck_id} deleted. Reason: {reason or DEFAULT_REASON_MESSAGE}"}


async def add_admin_service(email: str, admin_email: str):
    """
    Grants administrator privileges to a user.
    Logs the action.
    """
    user = await users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await users.update_one({"email": email}, {"$set": {"isAdmin": True}})

    await _log_admin_action(
        action="ADD_ADMIN",
        admin_email=admin_email,
        target_user_id=user["_id"],
        target_user_email=email,
    )
    return {"message": f"User {email} is now admin."}


async def remove_admin_service(email: str, admin_email: str):
    """
    Revokes administrator privileges from a user.
    Logs the action.
    """
    user = await users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await users.update_one({"email": email}, {"$set": {"isAdmin": False}})

    await _log_admin_action(
        action="REMOVE_ADMIN",
        admin_email=admin_email,
        target_user_id=user["_id"],
        target_user_email=email,
    )
    return {"message": f"User {email} is no more admin."}


async def delete_tag_service(tag: str, reason: str, admin_email: str):
    """
    Deletes a tag from all decks in the database.
    Logs the action.
    """
    await decks.update_many({"tags": tag}, {"$pull": {"tags": tag}})

    await _log_admin_action(
        action="DELETE_TAG",
        admin_email=admin_email,
        target_tag=tag,
        reason=reason or DEFAULT_REASON_MESSAGE,
    )
    return {"message": f"{tag} deleted. Reason: {reason or DEFAULT_REASON_MESSAGE}."}


async def clear_logs_service(admin_email: str):
    """
    Clears all administrative logs from the database.
    Logs the action.
    """
    await db.drop_collection("logs")

    await _log_admin_action(
        action="CLEAR_LOGS",
        admin_email=admin_email,
    )
    return {"message": "Logs cleared."}
