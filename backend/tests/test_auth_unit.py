import asyncio
from unittest.mock import AsyncMock, MagicMock

from backend.app.models import UserInDB
from backend.app.services.game_service import required_to_advance


async def test_register_new_user_succeeds(client, monkeypatch):
    mock_get_user = AsyncMock(return_value=None)
    mock_create_user = AsyncMock()
    mock_create_access_token = MagicMock(return_value="tok")
    mock_create_refresh_token = MagicMock(return_value="refresh")
    monkeypatch.setattr("backend.app.routers.auth.get_user", mock_get_user)
    monkeypatch.setattr("backend.app.routers.auth.create_user", mock_create_user)
    monkeypatch.setattr(
        "backend.app.routers.auth.create_access_token", mock_create_access_token
    )
    monkeypatch.setattr(
        "backend.app.routers.auth.create_refresh_token", mock_create_refresh_token
    )

    payload = {
        "name": "John",
        "surname": "Doe",
        "email": "john@example.com",
        "password": "pw",
    }
    response = await client.post("/api/auth/register", json=payload)
    assert response.status_code == 200
    mock_create_user.assert_called_once()
    assert mock_create_user.call_args.args[0].email == payload["email"]
    mock_create_access_token.assert_called_once()
    mock_create_refresh_token.assert_called_once()
    assert mock_create_access_token.call_args.kwargs["data"] == {
        "sub": payload["email"]
    }
    assert mock_create_refresh_token.call_args.kwargs["data"] == {
        "sub": payload["email"]
    }
    data = response.json()
    assert (
        data["token_type"] == "bearer"
        and data["access_token"]
        and data["refresh_token"] == "refresh"
    )


async def test_register_existing_email_fails(client, monkeypatch):
    mock_get_user = AsyncMock(return_value={"_id": "1"})
    monkeypatch.setattr("backend.app.routers.auth.get_user", mock_get_user)

    payload = {
        "name": "John",
        "surname": "Doe",
        "email": "john@example.com",
        "password": "pw",
    }
    response = await client.post("/api/auth/register", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


async def test_login_correct_credentials(client, monkeypatch):
    user = UserInDB(id="u1", name="A", surname="B", email="a@b.c", hashed_password="h")
    mock_auth = AsyncMock(return_value=user)
    mock_create_access_token = MagicMock(return_value="tok")
    mock_create_refresh_token = MagicMock(return_value="refresh")
    monkeypatch.setattr("backend.app.routers.auth.authenticate_user", mock_auth)
    monkeypatch.setattr(
        "backend.app.routers.auth.create_access_token", mock_create_access_token
    )
    monkeypatch.setattr(
        "backend.app.routers.auth.create_refresh_token", mock_create_refresh_token
    )

    response = await client.post(
        "/api/auth/login", data={"username": user.email, "password": "pw"}
    )

    assert response.status_code == 200
    mock_create_access_token.assert_called_once()
    mock_create_refresh_token.assert_called_once()
    assert mock_create_access_token.call_args.kwargs["data"] == {"sub": user.email}
    assert mock_create_refresh_token.call_args.kwargs["data"] == {"sub": user.email}
    body = response.json()
    assert (
        body["token_type"] == "bearer"
        and body["access_token"]
        and body["refresh_token"] == "refresh"
    )


async def test_refresh_token_endpoint(client, monkeypatch):
    user = UserInDB(id="u1", name="A", surname="B", email="a@b.c", hashed_password="h")
    mock_verify_refresh = AsyncMock(return_value=user)
    mock_create_access_token = MagicMock(return_value="newtok")
    mock_create_refresh_token = MagicMock(return_value="newrefresh")
    monkeypatch.setattr(
        "backend.app.routers.auth.verify_refresh_token", mock_verify_refresh
    )
    monkeypatch.setattr(
        "backend.app.routers.auth.create_access_token", mock_create_access_token
    )
    monkeypatch.setattr(
        "backend.app.routers.auth.create_refresh_token", mock_create_refresh_token
    )

    response = await client.post("/api/auth/refresh", json={"refresh_token": "r"})

    assert response.status_code == 200
    mock_verify_refresh.assert_called_once_with("r")
    mock_create_access_token.assert_called_once_with(data={"sub": user.email})
    mock_create_refresh_token.assert_called_once_with(data={"sub": user.email})
    body = response.json()
    assert body == {
        "access_token": "newtok",
        "refresh_token": "newrefresh",
        "token_type": "bearer",
    }


async def test_login_bad_credentials(client, monkeypatch):
    monkeypatch.setattr(
        "backend.app.routers.auth.authenticate_user", AsyncMock(return_value=None)
    )

    response = await client.post(
        "/api/auth/login", data={"username": "x", "password": "y"}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Incorrect email or password"


async def test_export_deck_txt(client, test_db, monkeypatch):
    await test_db.games.insert_one({"_id": "g1", "deck": ["a", "b", "c"]})
    response = await client.get("/api/game/leaderboard/g1/export")

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
