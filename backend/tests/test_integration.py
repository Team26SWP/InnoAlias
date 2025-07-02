import pytest

@pytest.mark.asyncio
async def test_end_to_end_auth_flow(client):
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
    assert r2.status_code == 200
    token = r2.json()["access_token"]
    r3 = await client.get(
        "/api/profile/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert r3.status_code == 200
    assert r3.json()["email"] == user["email"]


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
    assert user_doc and deck_doc["_id"] in user_doc.get("deck_ids", [])


@pytest.mark.asyncio
async def test_profile_requires_auth(client):
    res = await client.get("/api/profile/me")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_edit_deck_and_fetch_details(client):
    user = {
        "name": "Carl",
        "surname": "Jones",
        "email": "carl@example.com",
        "password": "pw",
    }
    await client.post("/api/auth/register", json=user)
    login = await client.post(
        "/api/auth/login",
        data={"username": user["email"], "password": user["password"]},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.post(
        "/api/profile/deck/save",
        json={"deck_name": "Colors", "words": ["red", "blue"], "tags": ["a"]},
        headers=headers,
    )
    deck_id = res.json()["inserted_id"]

    patch = await client.patch(
        f"/api/profile/deck/{deck_id}/edit",
        json={"deck_name": "Colors 2", "words": ["red", "green"], "tags": ["a", "b"]},
        headers=headers,
    )
    assert patch.status_code == 200
    assert patch.json()["name"] == "Colors 2"
    assert patch.json()["words"] == ["red", "green"]

    get_res = await client.get(f"/api/profile/deck/{deck_id}")
    assert get_res.status_code == 200
    assert get_res.json()["words"] == ["red", "green"]


@pytest.mark.asyncio
async def test_create_game_and_get_deck(client):
    payload = {
        "host_id": "h1",
        "number_of_teams": 1,
        "deck": ["alpha", "beta"],
        "time_for_guessing": 5,
        "tries_per_player": 0,
        "right_answers_to_advance": 1,
        "rotate_masters": False,
    }
    res = await client.post("/api/game/create", json=payload)
    assert res.status_code == 200
    game_id = res.json()["id"]

    deck_res = await client.get(f"/api/game/deck/{game_id}")
    assert deck_res.status_code == 200
    assert deck_res.json()["words"] == ["alpha", "beta"]
