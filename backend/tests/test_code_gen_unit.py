import pytest

from backend.app.code_gen import generate_deck_id, generate_game_code, generate_user_id


@pytest.mark.asyncio
async def test_generate_game_code_unique(test_db):
    await test_db.games.insert_one({"_id": "AAAAAA"})
    code = await generate_game_code()
    assert len(code) == 6 and code.isalnum() and code.isupper()
    assert code != "AAAAAA"


@pytest.mark.asyncio
async def test_generate_deck_id_digits(test_db):
    await test_db.decks.insert_one({"_id": "1234567890"})
    deck_id = await generate_deck_id()
    assert len(deck_id) == 10 and deck_id.isdigit()
    assert deck_id != "1234567890"


@pytest.mark.asyncio
async def test_generate_user_id_lowercase(test_db):
    await test_db.users.insert_one({"_id": "abc12345"})
    user_id = await generate_user_id()
    assert len(user_id) == 8 and user_id.isalnum()
    assert user_id != "abc12345"
    assert user_id == user_id.lower()
