import pytest
from datetime import datetime

from backend.app.services.game_service import process_new_word, manager


@pytest.mark.asyncio
async def test_process_new_word_finishes_empty(test_db):
    await test_db.games.insert_one(
        {"_id": "g1", "remaining_words": [], "state": "pending"}
    )
    result = await process_new_word("g1", 5)
    assert result["state"] == "finished"
    assert result["current_word"] is None
    assert result["remaining_words"] == []
    assert result["expires_at"] is None


@pytest.mark.asyncio
async def test_process_new_word_sets_next_word(test_db):
    await test_db.games.insert_one(
        {
            "_id": "g2",
            "remaining_words": ["one", "two"],
            "scores": {},
            "state": "pending",
            "rotate_masters": False,
            "current_master": None,
        }
    )
    manager.host_names["g2"] = "host"
    result = await process_new_word("g2", 1)
    assert result["state"] == "in_progress"
    assert result["current_word"] == "two"
    assert len(result["remaining_words"]) == 1
    assert result["current_master"] == "host"
    expires_at = result["expires_at"]
    assert isinstance(expires_at, datetime)


@pytest.mark.asyncio
async def test_process_new_word_team_independent(test_db):
    await test_db.games.insert_one(
        {
            "_id": "g3",
            "team_states": {
                "1": {"remaining_words": ["a"], "state": "pending"},
                "2": {"remaining_words": ["b"], "state": "pending"},
            },
            "team_count": 2,
            "scores": {},
            "state": "pending",
            "rotate_masters": False,
        }
    )

    r1 = await process_new_word("g3", 1, "1")
    assert r1["team_states"]["1"]["current_word"] == "a"
    assert r1["team_states"]["2"].get("current_word") is None

    r2 = await process_new_word("g3", 1, "2")
    assert r2["team_states"]["2"]["current_word"] == "b"
