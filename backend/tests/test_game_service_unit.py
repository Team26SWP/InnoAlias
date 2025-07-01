import pytest
from datetime import datetime

from backend.app.services.game_service import process_new_word, manager


@pytest.mark.asyncio
async def test_process_new_word_finishes_empty(test_db):
    await test_db.games.insert_one(
        {"_id": "g1", "teams": {"team_1": {"id": "team_1", "remaining_words": [], "state": "pending", "players": [], "current_master": None, "scores": {}}}, "game_state": "pending"}
    )
    result = await process_new_word("g1", "team_1", 5)
    assert result["teams"]["team_1"]["state"] == "finished"
    assert result["teams"]["team_1"]["current_word"] is None
    assert result["teams"]["team_1"]["expires_at"] is None
    assert result["game_state"] == "finished"


@pytest.mark.asyncio
async def test_process_new_word_sets_next_word(test_db):
    await test_db.games.insert_one(
        {
            "_id": "g2",
            "teams": {
                "team_1": {
                    "id": "team_1",
                    "remaining_words": ["one", "two"],
                    "scores": {},
                    "state": "pending",
                    "players": ["player1"],
                    "current_master": "player1",
                }
            },
            "game_state": "pending",
            "rotate_masters": False,
        }
    )
    result = await process_new_word("g2", "team_1", 1)
    assert result["teams"]["team_1"]["state"] == "in_progress"
    assert result["teams"]["team_1"]["current_word"] == "one"
    assert len(result["teams"]["team_1"]["remaining_words"]) == 1
    assert result["teams"]["team_1"]["current_master"] == "player1"
    expires_at = result["teams"]["team_1"]["expires_at"]
    assert isinstance(expires_at, datetime)
