import asyncio
from unittest.mock import AsyncMock, MagicMock

from backend.app.models import UserInDB
from backend.app.services.game_service import required_to_advance


def test_register_new_user_succeeds(sync_client, monkeypatch):
    mock_get_user = AsyncMock(return_value=None)
    mock_create_user = AsyncMock()
    mock_create_access_token = MagicMock(return_value="tok")
    monkeypatch.setattr("backend.app.routers.auth.get_user", mock_get_user)
    monkeypatch.setattr("backend.app.routers.auth.create_user", mock_create_user)
    monkeypatch.setattr(
        "backend.app.routers.auth.create_access_token", mock_create_access_token
    )

    payload = {
        "name": "John",
        "surname": "Doe",
        "email": "john@example.com",
        "password": "pw",
    }
    response = sync_client.post("/api/auth/register", json=payload)

    assert response.status_code == 200
    mock_create_user.assert_called_once()
    assert mock_create_user.call_args.args[0].email == payload["email"]
    mock_create_access_token.assert_called_once()
    assert mock_create_access_token.call_args.kwargs["data"] == {
        "sub": payload["email"]
    }
    data = response.json()
    assert data["token_type"] == "bearer" and data["access_token"]


def test_register_existing_email_fails(sync_client, monkeypatch):
    mock_get_user = AsyncMock(return_value={"_id": "1"})
    monkeypatch.setattr("backend.app.routers.auth.get_user", mock_get_user)

    payload = {
        "name": "John",
        "surname": "Doe",
        "email": "john@example.com",
        "password": "pw",
    }
    response = sync_client.post("/api/auth/register", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


# 3 Login with correct credentials returns token
def test_login_correct_credentials(sync_client, monkeypatch):
    user = UserInDB(id="u1", name="A", surname="B", email="a@b.c", hashed_password="h")
    mock_auth = AsyncMock(return_value=user)
    mock_create_access_token = MagicMock(return_value="tok")
    monkeypatch.setattr("backend.app.routers.auth.authenticate_user", mock_auth)
    monkeypatch.setattr(
        "backend.app.routers.auth.create_access_token", mock_create_access_token
    )

    response = sync_client.post(
        "/api/auth/login", data={"username": user.email, "password": "pw"}
    )

    assert response.status_code == 200
    mock_create_access_token.assert_called_once()
    assert mock_create_access_token.call_args.kwargs["data"] == {"sub": user.email}
    body = response.json()
    assert body["token_type"] == "bearer" and body["access_token"]


def test_login_bad_credentials(sync_client, monkeypatch):
    monkeypatch.setattr(
        "backend.app.routers.auth.authenticate_user", AsyncMock(return_value=None)
    )

    response = sync_client.post(
        "/api/auth/login", data={"username": "x", "password": "y"}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Incorrect email or password"


def test_export_deck_txt(sync_client, test_db, monkeypatch):
    asyncio.get_event_loop().run_until_complete(
        test_db.games.insert_one({"_id": "g1", "deck": ["a", "b", "c"]})
    )
    response = sync_client.get("/api/game/leaderboard/g1/export")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "exported_deck_" in response.headers.get("content-disposition", "")
    assert response.text == "a\nb\nc"


def test_required_to_advance_logic():
    state = {
        "scores": {"alice": 1, "bob": 2, "carol": 3},
        "current_master": "alice",
        "right_answers_to_advance": 3,
    }
    assert required_to_advance(state) == 2
