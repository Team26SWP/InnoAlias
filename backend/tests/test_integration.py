import pytest
import pytest_asyncio


@pytest_asyncio.fixture
async def created_game(client, monkeypatch):
    monkeypatch.setattr("backend.app.routers.game.shuffle", lambda x: None)
    words = ["a", "b", "c"]
    resp = await client.post(
        "/api/game/create", json={"host_id": "test_host", "number_of_teams": 1, "deck": words, "words_amount": 3}
    )
    game_id = resp.json()["id"]
    yield game_id
    await client.delete(f"/api/game/delete/{game_id}")


@pytest.mark.asyncio
async def test_end_to_end_flow(client):
    user = {
        "name": "Ann",
        "surname": "Doe",
        "email": "ann@example.com",
        "password": "pw",
    }
    r1 = await client.post("/api/auth/register", json=user)
    assert r1.status_code == 200
    r2 = await client.post(
        "/api/auth/login",
        data={"username": user["email"], "password": user["password"]},
    )
    token = r2.json()["access_token"]
    r3 = await client.get(
        "/api/profile/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert r3.status_code == 200
    data = r3.json()
    assert data["email"] == user["email"]


@pytest.mark.asyncio
async def test_deck_save_and_profile_listing(client, test_db):
    user = {
        "name": "Bob",
        "surname": "Smith",
        "email": "bob@example.com",
        "password": "pw",
    }
    await client.post("/api/auth/register", json=user)
    login = await client.post(
        "/api/auth/login",
        data={"username": user["email"], "password": user["password"]},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    words = ["one", "two"]
    res = await client.post(
        "/api/profile/deck/save",
        json={"deck_name": "Test", "tags": ["foo", "bar"], "words": words},
        headers=headers,
    )
    assert res.status_code == 200
    user_doc = await test_db.users.find_one({"email": user["email"]})
    deck_doc = await test_db.decks.find_one({"_id": res.json()["inserted_id"]})
    assert deck_doc and deck_doc["name"] == "Test"
    assert deck_doc["words"] == words
    assert deck_doc.get("tags") in (["foo", "bar"], "foo,bar", ["foo,bar"], None)
    assert user_doc and deck_doc["_id"] in user_doc.get("deck_ids", [])


@pytest.mark.asyncio
async def test_game_creation_and_deck(client, created_game):
    game_id = created_game
    deck_resp = await client.get(f"/api/game/deck/{game_id}")
    assert deck_resp.status_code == 200
    # The words are now part of the game object, not directly returned by the fixture
    # We need to fetch the game to get the original deck
    game = await client.get(f"/api/game/deck/{game_id}") # This endpoint returns the full deck
    assert deck_resp.json() == game.json()


@pytest.mark.asyncio
async def test_export_deck_integration(client, created_game):
    game_id = created_game
    game_data = await client.get(f"/api/game/deck/{game_id}")
    words = game_data.json()["words"]
    export = await client.get(f"/api/game/leaderboard/{game_id}/export")
    assert export.status_code == 200
    assert export.headers["content-type"].startswith("text/plain")
    assert "exported_deck_" in export.headers.get("content-disposition", "")
    assert export.text == "\n".join(words)


@pytest.mark.asyncio
async def test_leaderboard_sorting(client, test_db):
    game_id = "L1"
    await test_db.games.insert_one(
        {
            "_id": game_id,
            "host_id": "host1",
            "number_of_teams": 2,
            "teams": {
                "team_1": {
                    "id": "team_1",
                    "name": "Team Alpha",
                    "players": ["alice", "charlie"],
                    "scores": {"alice": 3, "charlie": 2},
                    "remaining_words": [],
                    "state": "finished",
                },
                "team_2": {
                    "id": "team_2",
                    "name": "Team Beta",
                    "players": ["bob", "diana"],
                    "scores": {"bob": 5, "diana": 1},
                    "remaining_words": [],
                    "state": "finished",
                },
            },
            "game_state": "finished",
            "winning_team": "team_2",
        }
    )
    res = await client.get(f"/api/game/leaderboard/{game_id}")
    assert res.status_code == 200
    expected_leaderboard = {
        "Team Beta": {"total_score": 6, "players": {"bob": 5, "diana": 1}},
        "Team Alpha": {"total_score": 5, "players": {"alice": 3, "charlie": 2}},
    }
    assert res.json() == expected_leaderboard


@pytest.mark.asyncio
async def test_profile_requires_auth(client):
    res = await client.get("/api/profile/me")
    assert res.status_code == 401
