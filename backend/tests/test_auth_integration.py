import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login_success(client: AsyncClient, test_db):
    # Test registration
    register_data = {
        "name": "Integration",
        "surname": "Test",
        "email": "integration@example.com",
        "password": "IntegrationPassword1!",
    }
    response = await client.post("/api/auth/register", json=register_data)
    assert response.status_code == 200
    register_response_data = response.json()
    assert "access_token" in register_response_data
    assert "refresh_token" in register_response_data
    assert register_response_data["token_type"] == "bearer"

    # Verify user exists in the mock database
    user_in_db = await test_db.users.find_one({"email": "integration@example.com"})
    assert user_in_db is not None
    assert user_in_db["email"] == "integration@example.com"

    # Test login with the registered user
    login_data = {
        "username": "integration@example.com",
        "password": "IntegrationPassword1!",
    }
    response = await client.post("/api/auth/login", data=login_data)
    assert response.status_code == 200
    login_response_data = response.json()
    assert "access_token" in login_response_data
    assert "refresh_token" in login_response_data
    assert login_response_data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_existing_email(client: AsyncClient, test_db):
    # Register a user first
    register_data = {
        "name": "Existing",
        "surname": "User",
        "email": "existing@example.com",
        "password": "ExistingPassword1!",
    }
    await client.post("/api/auth/register", json=register_data)

    # Try to register again with the same email
    response = await client.post("/api/auth/register", json=register_data)
    assert response.status_code == 400
    assert response.json() == {"detail": "Email already registered"}


@pytest.mark.asyncio
async def test_login_incorrect_credentials(client: AsyncClient, test_db):
    # Attempt login with non-existent user
    login_data = {"username": "nonexistent@example.com", "password": "fakepassword"}
    response = await client.post("/api/auth/login", data=login_data)
    assert response.status_code == 400
    assert response.json() == {"detail": "Incorrect email or password"}

    # Register a user
    register_data = {
        "name": "Login",
        "surname": "Test",
        "email": "login@example.com",
        "password": "LoginPassword1!",
    }
    await client.post("/api/auth/register", json=register_data)

    # Attempt login with correct email but wrong password
    wrong_password_data = {"username": "login@example.com", "password": "wrongpassword"}
    response = await client.post("/api/auth/login", data=wrong_password_data)
    assert response.status_code == 400
    assert response.json() == {"detail": "Incorrect email or password"}


@pytest.mark.asyncio
async def test_refresh_token_success(client: AsyncClient, test_db):
    # Register a user to get tokens
    register_data = {
        "name": "Refresh",
        "surname": "User",
        "email": "refresh@example.com",
        "password": "RefreshPassword1!",
    }
    response = await client.post("/api/auth/register", json=register_data)
    refresh_token = response.json()["refresh_token"]

    # Use the refresh token to get new tokens
    response = await client.post(
        "/api/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert response.status_code == 200
    refresh_response_data = response.json()
    assert "access_token" in refresh_response_data
    assert "refresh_token" in refresh_response_data
    assert refresh_response_data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_refresh_token_invalid(client: AsyncClient):
    response = await client.post(
        "/api/auth/refresh", json={"refresh_token": "invalid_token"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_refresh_token_expired(client: AsyncClient, test_db):
    # Manually create an expired refresh token for a dummy user
    from backend.app.services.auth_service import create_refresh_token
    from datetime import timedelta

    expired_refresh_token = create_refresh_token(
        {"sub": "dummy@example.com"}, expires_delta=timedelta(days=-1)
    )

    response = await client.post(
        "/api/auth/refresh", json={"refresh_token": expired_refresh_token}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Token has expired"}
