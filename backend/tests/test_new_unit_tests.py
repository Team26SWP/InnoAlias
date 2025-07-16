import pytest

from backend.app.models import AIGame, AIGameSettings
from backend.app.services.auth_service import verify_password, create_user
from backend.app.models import User
from backend.app.services.game_service import reassign_master
from backend.app.code_gen import generate_game_code, generate_user_id
from backend.app.services.aigame_service import create_aigame


@pytest.mark.asyncio
async def test_password_hashing_and_verification(test_db):
    user = User(
        name="test",
        surname="user",
        email="test@example.com",
        password="TestPassword1!",
    )
    created_user = await create_user(user)
    assert verify_password("TestPassword1!", created_user["hashed_password"])
    assert not verify_password("wrong_password", created_user["hashed_password"])


@pytest.mark.asyncio
async def test_reassign_master_rotation(test_db, monkeypatch):
    monkeypatch.setattr("backend.app.services.game_service.choice", lambda x: "p3")
    await test_db.games.insert_one(
        {
            "_id": "game_reassign_master_rotation",
            "teams": {
                "team_1": {
                    "players": ["p1", "p2", "p3"],
                    "current_master": "p2",
                }
            },
            "rotate_masters": True,
        }
    )
    await reassign_master("game_reassign_master_rotation", "team_1")
    game = await test_db.games.find_one({"_id": "game_reassign_master_rotation"})
    assert game["teams"]["team_1"]["current_master"] == "p3"


@pytest.mark.asyncio
async def test_generate_multiple_unique_ids(test_db):
    game_codes = {await generate_game_code() for _ in range(3)}
    assert len(game_codes) == 3
    user_ids = {await generate_user_id() for _ in range(3)}
    assert len(user_ids) == 3


@pytest.mark.asyncio
async def test_create_ai_game(test_db, monkeypatch):
    await test_db.aigames.delete_many({})

    async def mock_generate_aigame_code():
        return "AIGAME"

    monkeypatch.setattr(
        "backend.app.services.aigame_service.generate_aigame_code",
        mock_generate_aigame_code,
    )

    monkeypatch.setattr(
        "backend.app.services.aigame_service.aigames",
        test_db.aigames,
    )

    game_settings = AIGameSettings(
        time_for_guessing=10,
        word_amount=5,
    )
    game = AIGame(
        player_id="test_player",
        deck=["word1", "word2", "word3", "word4", "word5", "word6"],
        settings=game_settings,
    )
    game_id = await create_aigame(game)
    assert game_id == "AIGAME"


@pytest.mark.asyncio
async def test_reassign_master_no_rotation(test_db):
    await test_db.games.insert_one(
        {
            "_id": "game_reassign_master_no_rotation",
            "teams": {
                "team_1": {
                    "players": ["p1", "p2"],
                    "current_master": "p1",
                }
            },
            "rotate_masters": False,
        }
    )
    await reassign_master("game_reassign_master_no_rotation", "team_1")
    game = await test_db.games.find_one({"_id": "game_reassign_master_no_rotation"})
    assert game["teams"]["team_1"]["current_master"] == "p1"
