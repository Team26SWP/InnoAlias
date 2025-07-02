import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
import asyncio


@pytest.mark.asyncio
async def test_full_game_flow():
    client = TestClient(app)
    game_creation_response = client.post(
        "/api/game/create",
        json={
            "host_id": "host123",
            "number_of_teams": 2,
            "deck": ["word1", "word2", "word3"],
            "time_for_guessing": 5,
            "tries_per_player": 1,
            "rotate_masters": True,
            "right_answers_to_advance": 1,
        },
    )
    assert game_creation_response.status_code == 200
    game_id = game_creation_response.json()["id"]

    with client.websocket_connect(
        f"/api/game/{game_id}?id=host123"
    ) as host_ws, client.websocket_connect(
        f"/api/game/player/{game_id}?name=p1&team_id=team_1"
    ) as p1_ws, client.websocket_connect(
        f"/api/game/player/{game_id}?name=p2&team_id=team_1"
    ) as p2_ws, client.websocket_connect(
        f"/api/game/player/{game_id}?name=p3&team_id=team_2"
    ) as p3_ws, client.websocket_connect(
        f"/api/game/player/{game_id}?name=p4&team_id=team_2"
    ) as p4_ws:

        for ws in [host_ws, p1_ws, p2_ws, p3_ws, p4_ws]:
            data = ws.receive_json()
            assert data["game_state"] == "pending"

        host_ws.send_json({"action": "start_game"})

        await asyncio.sleep(1)

        p1_state = p1_ws.receive_json()
        assert p1_state["game_state"] == "in_progress"
        current_master = p1_state["current_master"]
        current_word = p1_state["current_word"]

        guesser_ws = p2_ws if current_master == "p1" else p1_ws

        guesser_ws.send_json({"action": "guess", "guess": current_word})

        await asyncio.sleep(1)
        host_ws.send_json({"action": "stop_game"})

        await asyncio.sleep(1)

        final_state = host_ws.receive_json()
        assert final_state["game_state"] == "finished"
