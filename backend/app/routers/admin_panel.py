from datetime import datetime

from fastapi import HTTPException, Depends
from fastapi import APIRouter

from backend.app.db import db
from backend.app.services.auth_service import users, get_current_user
from backend.app.services.game_service import decks

router = APIRouter(prefix="", tags=["admin"])


logs = db.logs


@router.delete("/delete/user/{user_id}")
async def delete_user(
    user_id: str,
    reason: str,
    current_user=Depends(get_current_user),
):
    if not current_user.isAdmin:
        raise HTTPException(status_code=403, detail="Forbidden")
    user = await users.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    log = {
        "action": "DELETE_USER",
        "admin_id": current_user.id,
        "target_user_id": user_id,
        "reason": reason,
        "timestamp": datetime.now().isoformat(),
    }
    await users.delete_one({"user_id": user_id})
    await decks.update_many(
        {"owner_ids": user["_id"]}, {"$pull": {"owner_ids": user["_id"]}}
    )
    await logs.insert_one(log)

    return {"message": f"{user_id} deleted. Reason: {reason}."}


@router.get("/logs")
async def get_logs(current_user=Depends(get_current_user)):
    if not current_user.isAdmin:
        raise HTTPException(status_code=403, detail="Forbidden")
    show_logs = await logs.find()
    if not show_logs:
        raise HTTPException(status_code=404, detail="No logs")
    return {"logs": show_logs}


@router.delete("/delete/deck/{deck_id}")
async def delete_deck(deck_id, reason: str, current_user=Depends(get_current_user)):
    if not current_user.isAdmin:
        raise HTTPException(status_code=403, detail="Forbidden")
    deck = await decks.find_one({"deck_id": deck_id})
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    await decks.delete_one({"deck_id": deck_id})
    await users.update_many({"deck_ids": deck_id}, {"$pull": {"deck_ids": deck_id}})
    log = {
        "action": "DELETE_DECK",
        "admin_id": current_user.id,
        "target_deck_id": deck_id,
        "reason": reason,
        "timestamp": datetime.now().isoformat(),
    }
    await logs.insert_one(log)
    return {"message": f"{deck_id} deleted. Reason: {reason}"}


@router.put("/add/{user_id}")
async def add_admin(
    user_id: str,
    current_user=Depends(get_current_user),
):
    if not current_user.isAdmin:
        raise HTTPException(status_code=403, detail="Forbidden")
    user = await users.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await users.update_one({"user_id": user_id}, {"$set": {"isAdmin": True}})
    log = {
        "action": "ADD_ADMIN",
        "admin_id": current_user.id,
        "target_user_id": user["_id"],
        "timestamp": datetime.now().isoformat(),
    }
    await logs.insert_one(log)
    return {"message": f"User {user["_id"]} is now admin."}


@router.put("/remove/{user_id}")
async def remove_admin(
    user_id: str,
    current_user=Depends(get_current_user),
):
    if not current_user.isAdmin:
        raise HTTPException(status_code=403, detail="Forbidden")
    user = await users.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await users.update_one({"user_id": user_id}, {"$set": {"isAdmin": False}})
    log = {
        "action": "REMOVE_ADMIN",
        "admin_id": current_user.id,
        "target_user_id": user["_id"],
        "timestamp": datetime.now().isoformat(),
    }
    await logs.insert_one(log)
    return {"message": f"User {user["_id"]} is no more admin."}


@router.delete("/delete/tag/{tag}")
async def delete_tag(
    tag: str,
    reason: str,
    current_user=Depends(get_current_user),
):
    if not current_user.isAdmin:
        raise HTTPException(status_code=403, detail="Forbidden")
    await decks.update_many({"tags": tag}, {"$pull": {"tags": tag}})
    log = {
        "action": "DELETE_TAG",
        "admin_id": current_user.id,
        "target_tag": tag,
        "reason": reason,
        "timestamp": datetime.now().isoformat(),
    }
    await logs.insert_one(log)
    return {"message": f"{tag} deleted. Reason: {reason}."}


@router.delete("/clear/logs")
async def clear_logs(current_user=Depends(get_current_user)):
    if not current_user.isAdmin:
        raise HTTPException(status_code=403, detail="Forbidden")
    await db.drop_collection("logs")
    log = {
        "action": "CLEAR_LOGS",
        "admin_id": current_user.id,
        "timestamp": datetime.now().isoformat(),
    }
    await logs.insert_one(log)
    return {"message": "Logs cleared."}
