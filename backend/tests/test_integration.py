1import pytest


@pytest.mark.asyncio
async def test_end_to_end_auth_flow(client):
    user = {
        "name": "Ann",
        "surname": "Doe",
        "email": "ann@example.com",
        "password": "pw",
        "isAdmin": "true"
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
        "isAdmin": "true"
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
        "isAdmin": "true"
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
    assert set(deck_res.json()["words"]) == {"alpha", "beta"}


@pytest.mark.asyncio
async def test_delete_deck_removes_from_profile(client, test_db):
    user = {
        "name": "Del",
        "surname": "User",
        "email": "del@example.com",
        "password": "pw",
        "isAdmin": "true"
    }
    await client.post("/api/auth/register", json=user)
    login = await client.post(
        "/api/auth/login",
        data={"username": user["email"], "password": user["password"]},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    save = await client.post(
        "/api/profile/deck/save",
        json={"deck_name": "DelDeck", "words": ["x"], "tags": []},
        headers=headers,
    )
    deck_id = save.json()["inserted_id"]

    delete_res = await client.delete(
        f"/api/profile/deck/{deck_id}/delete", headers=headers
    )
    assert delete_res.status_code == 200
    assert await test_db.decks.find_one({"_id": deck_id}) is None
    user_doc = await test_db.users.find_one({"email": user["email"]})
    assert deck_id not in user_doc.get("deck_ids", [])


@pytest.mark.asyncio
async def test_delete_deck_requires_auth(client):
    res = await client.delete("/api/profile/deck/unknown/delete")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_profile_forbidden_for_other_user(client, test_db):
    user1 = {"name": "A", "surname": "B", "email": "a@example.com", "password": "pw", "isAdmin": "true"}
    user2 = {"name": "C", "surname": "D", "email": "c@example.com", "password": "pw", "isAdmin": "true"}
    await client.post("/api/auth/register", json=user1)
    await client.post("/api/auth/register", json=user2)
    login = await client.post(
        "/api/auth/login", data={"username": user1["email"], "password": "pw"}
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    other = await test_db.users.find_one({"email": user2["email"]})
    res = await client.get(f"/api/profile/{other['_id']}", headers=headers)
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_edit_deck_forbidden_for_non_owner(client, test_db):
    owner = {
        "name": "O",
        "surname": "U",
        "email": "owner@example.com",
        "password": "pw",
        "isAdmin": "true"
    }
    attacker = {"name": "H", "surname": "T", "email": "h@example.com", "password": "pw"}
    await client.post("/api/auth/register", json=owner)
    await client.post("/api/auth/register", json=attacker)

    login_owner = await client.post(
        "/api/auth/login", data={"username": owner["email"], "password": "pw"}
    )
    owner_token = login_owner.json()["access_token"]
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    save = await client.post(
        "/api/profile/deck/save",
        json={"deck_name": "Sec", "words": ["a"], "tags": []},
        headers=owner_headers,
    )
    deck_id = save.json()["inserted_id"]

    login_attacker = await client.post(
        "/api/auth/login", data={"username": attacker["email"], "password": "pw"}
    )
    att_token = login_attacker.json()["access_token"]
    att_headers = {"Authorization": f"Bearer {att_token}"}
    res = await client.patch(
        f"/api/profile/deck/{deck_id}/edit",
        json={"deck_name": "Hack"},
        headers=att_headers,
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_get_game_leaderboard(client, test_db):
    await test_db.games.insert_one(
        {
            "_id": "lb1",
            "teams": {
                "team_1": {"name": "Team 1", "scores": {"alice": 2, "bob": 1}},
                "team_2": {"name": "Team 2", "scores": {"carl": 4}},
            },
        }
    )

    res = await client.get("/api/game/leaderboard/lb1")
    assert res.status_code == 200
    data = res.json()
    assert list(data.keys()) == ["Team 2", "Team 1"]
    assert data["Team 2"]["total_score"] == 4
    assert data["Team 1"]["players"] == {"alice": 2, "bob": 1}
