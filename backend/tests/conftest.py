import mongomock_motor
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

import backend.app.code_gen as code_gen
import backend.app.db as db_module
import backend.app.routers.game as game_router
import backend.app.services.auth_service as auth_service
import backend.app.services.game_service as game_service
import backend.app.services.profile_service as profile_service
import backend.tests._test_setup  # noqa: F401
from backend.app.main import app as fastapi_app


@pytest_asyncio.fixture
async def test_db(monkeypatch):
    client = mongomock_motor.AsyncMongoMockClient()
    test_db = client.db
    monkeypatch.setattr(db_module, "db", test_db)
    monkeypatch.setattr(auth_service, "users", test_db.users)
    monkeypatch.setattr(game_service, "games", test_db.games)
    monkeypatch.setattr(game_service, "decks", test_db.decks)
    monkeypatch.setattr(game_router, "games", test_db.games)
    monkeypatch.setattr(profile_service, "users", test_db.users)
    monkeypatch.setattr(profile_service, "decks", test_db.decks)
    monkeypatch.setattr(code_gen, "games", test_db.games)
    monkeypatch.setattr(code_gen, "decks", test_db.decks)
    monkeypatch.setattr(code_gen, "users", test_db.users)
    yield test_db


@pytest_asyncio.fixture
async def client(test_db):
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
