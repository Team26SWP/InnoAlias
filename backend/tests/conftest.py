import backend.tests._test_setup  # noqa: F401
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient
import mongomock_motor

from backend.app.main import app as fastapi_app
import backend.app.services.auth_service as auth_service
import backend.app.routers.profile as profile_router
import backend.app.db as db_module
import backend.app.services.game_service as game_service
import backend.app.routers.game as game_router
import backend.app.code_gen as code_gen


@pytest_asyncio.fixture
async def test_db(monkeypatch):
    client = mongomock_motor.AsyncMongoMockClient()
    test_db = client.db
    monkeypatch.setattr(db_module, "db", test_db)
    monkeypatch.setattr(auth_service, "users", test_db.users)
    monkeypatch.setattr(game_service, "games", test_db.games)
    monkeypatch.setattr(game_service, "decks", test_db.decks)
    monkeypatch.setattr(game_router, "games", test_db.games)
    monkeypatch.setattr(game_router, "db", test_db)
    monkeypatch.setattr(profile_router, "db", test_db)
    monkeypatch.setattr(code_gen, "games", test_db.games)
    monkeypatch.setattr(code_gen, "decks", test_db.decks)
    monkeypatch.setattr(code_gen, "users", test_db.users)
    yield test_db


@pytest_asyncio.fixture
async def client(test_db):
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def sync_client(test_db):
    with TestClient(fastapi_app) as c:
        yield c
