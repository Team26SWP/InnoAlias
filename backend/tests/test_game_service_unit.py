import pytest
from datetime import datetime
from backend.app.services.game_service import (
    process_new_word,
    add_player_to_game,
    remove_player_from_game,
    reassign_master,
)


@pytest.mark.asyncio
async def test_add_player_to_game(test_db):
    await test_db.games.insert_one(
        {
            "_id": "game_add_player",
            "teams": {"team_1": {"players": [], "scores": {}}},
            "rotate_masters": False,
        }
    )
    game = await add_player_to_game("game_add_player", "player1", "team_1")
    assert "player1" in game["teams"]["team_1"]["players"]
    assert game["teams"]["team_1"]["scores"]["player1"] == 0
    assert game["teams"]["team_1"]["current_master"] == "player1"


@pytest.mark.asyncio
async def test_remove_player_from_game(test_db):
    await test_db.games.insert_one(
        {
            "_id": "game_remove_player",
            "teams": {
                "team_1": {
                    "players": ["player1", "player2"],
                    "scores": {"player1": 10, "player2": 5},
                    "current_master": "player1",
                }
            },
            "rotate_masters": False,
        }
    )
    game = await remove_player_from_game("game_remove_player", "player1", "team_1")
    assert "player1" not in game["teams"]["team_1"]["players"]
    assert "player1" not in game["teams"]["team_1"]["scores"]
    assert game["teams"]["team_1"]["current_master"] == "player2"


@pytest.mark.asyncio
async def test_reassign_master(test_db):
    await test_db.games.insert_one(
        {
            "_id": "game_reassign_master",
            "teams": {"team_1": {"players": ["p1", "p2"], "current_master": "p1"}},
            "rotate_masters": True,
        }
    )
    await reassign_master("game_reassign_master", "team_1")
    game = await test_db.games.find_one({"_id": "game_reassign_master"})
    assert game["teams"]["team_1"]["current_master"] in ["p1", "p2"]


@pytest.mark.asyncio
async def test_process_new_word_finishes_game_when_all_teams_done(test_db):
    await test_db.games.insert_one(
        {
            "_id": "g1_all_finish",
            "teams": {
                "team_1": {
                    "id": "team_1",
                    "remaining_words": [],
                    "state": "in_progress",
                    "players": [],
                    "scores": {},
                },
                "team_2": {
                    "id": "team_2",
                    "remaining_words": [],
                    "state": "finished",
                    "players": [],
                    "scores": {"p1": 5},
                },
            },
            "game_state": "in_progress",
        }
    )
    result = await process_new_word("g1_all_finish", "team_1", 5)
    assert result["game_state"] == "finished"
    assert result["winning_team"] == "team_2"


@pytest.mark.asyncio
async def test_process_new_word_sets_next_word(test_db):
    await test_db.games.insert_one(
        {
            "_id": "g2_next_word",
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
    result = await process_new_word("g2_next_word", "team_1", 1)
    assert result["teams"]["team_1"]["state"] == "in_progress"
    assert result["teams"]["team_1"]["current_word"] == "one"
    assert len(result["teams"]["team_1"]["remaining_words"]) == 1
    assert isinstance(result["teams"]["team_1"]["expires_at"], datetime)
