import pytest
import pytest_asyncio

# helper fixture to create a game and return id and words
@pytest_asyncio.fixture
async def created_game(client, monkeypatch):
    monkeypatch.setattr("backend.app.routers.game.shuffle", lambda x: None)
    words = ["a", "b", "c"]
    resp = await client.post("/api/game/create", json={"remaining_words": words, "words_amount": 3})
    game_id = resp.json()["id"]
    return game_id, words

# 1 End-to-end user flow
@pytest.mark.asyncio
async def test_end_to_end_flow(client):
    user = {"name": "Ann", "surname": "Doe", "email": "ann@example.com", "password": "pw"}
    r1 = await client.post("/api/auth/register", json=user)
    assert r1.status_code == 200
    r2 = await client.post("/api/auth/login", data={"username": user["email"], "password": user["password"]})
    token = r2.json()["access_token"]
    r3 = await client.get("/api/profile/me", headers={"Authorization": f"Bearer {token}"})
    assert r3.status_code == 200
    data = r3.json()
    assert data["email"] == user["email"]

# 2 Deck save & profile listing
@pytest.mark.asyncio
async def test_deck_save_and_profile_listing(client, test_db):
    user = {"name": "Bob", "surname": "Smith", "email": "bob@example.com", "password": "pw"}
    await client.post("/api/auth/register", json=user)
    login = await client.post("/api/auth/login", data={"username": user["email"], "password": user["password"]})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    words = {"w1": "one", "w2": "two"}
    res = await client.post(
        "/api/game/g1/deck/save?deck_name=Test&tags=foo,bar",
        json={"words": words},
        headers=headers,
    )
    assert res.status_code == 200
    user_doc = await test_db.users.find_one({"email": user["email"]})
    deck_doc = await test_db.decks.find_one({"_id": res.json()["inserted_id"]})
    assert deck_doc and deck_doc["name"] == "Test"
    assert deck_doc["words"] == words
    assert deck_doc.get("tags") in (["foo", "bar"], "foo,bar", ["foo,bar"], None)
    assert user_doc and deck_doc["_id"] in user_doc.get("deck_ids", [])

# 3 Game creation and deck retrieval
@pytest.mark.asyncio
async def test_game_creation_and_deck(client, created_game):
    game_id, words = created_game
    deck_resp = await client.get(f"/api/game/{game_id}/deck")
    assert deck_resp.status_code == 200
    assert deck_resp.json() == {"words": words}

# 4 Export deck integration
@pytest.mark.asyncio
async def test_export_deck_integration(client, created_game):
    game_id, words = created_game
    export = await client.get(f"/api/game/leaderboard/{game_id}/export")
    assert export.status_code == 200
    assert export.headers["content-type"].startswith("text/plain")
    assert "exported_deck_" in export.headers.get("content-disposition", "")
    assert export.text == "\n".join(words)

# 5 Leaderboard sorting
@pytest.mark.asyncio
async def test_leaderboard_sorting(client, test_db):
    await test_db.games.insert_one({"_id": "L1", "scores": {"alice": 3, "bob": 5, "carol": 2}})
    res = await client.get("/api/game/leaderboard/L1")
    assert res.status_code == 200
    assert list(res.json().keys()) == ["bob", "alice", "carol"]

# additional integration: unauthorized profile access
@pytest.mark.asyncio
async def test_profile_requires_auth(client):
    res = await client.get("/api/profile/me")
    assert res.status_code == 401
