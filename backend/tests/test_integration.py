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
