from unittest.mock import AsyncMock, patch

import mongomock_motor
import pytest
from fastapi.testclient import TestClient

import backend.app.code_gen as code_gen
import backend.app.db as db_module
import backend.app.routers.game as game_router
import backend.app.services.auth_service as auth_service
import backend.app.services.game_service as game_service
import backend.app.services.profile_service as profile_service
import backend.tests._test_setup  # noqa: F401
from backend.app.main import app
from backend.app.services.auth_service import get_current_user

client_mock: mongomock_motor.AsyncMongoMockClient = (
    mongomock_motor.AsyncMongoMockClient()
)
test_db = client_mock.db
db_module.db = test_db
auth_service.users = test_db.users
game_service.games = test_db.games
game_service.decks = test_db.decks
game_router.games = test_db.games
profile_service.users = test_db.users
profile_service.decks = test_db.decks
code_gen.games = test_db.games
code_gen.decks = test_db.decks
code_gen.users = test_db.users

client = TestClient(app)


@pytest.fixture
def admin_user():
    return {"email": "admin@test.com", "isAdmin": True, "_id": "admin_id"}


@pytest.fixture
def normal_user():
    return {"email": "user@test.com", "isAdmin": False, "_id": "user_id"}


def override_get_current_user_admin():
    return {"email": "admin@test.com", "isAdmin": True, "_id": "admin_id"}


def override_get_current_user_normal():
    return {"email": "user@test.com", "isAdmin": False, "_id": "user_id"}


@patch("backend.app.routers.admin_panel.delete_user_service", new_callable=AsyncMock)
def test_delete_user_by_admin(mock_delete_user_service, admin_user):
    app.dependency_overrides[get_current_user] = override_get_current_user_admin
    mock_delete_user_service.return_value = {"message": "User user@test.com deleted."}

    response = client.delete("/api/admin/delete/user/user@test.com?reason=test")
    assert response.status_code == 200
    assert response.json() == {"message": "User user@test.com deleted."}
    mock_delete_user_service.assert_called_once_with(
        "user@test.com", "test", "admin@test.com"
    )


def test_delete_user_by_normal_user(normal_user):
    app.dependency_overrides[get_current_user] = override_get_current_user_normal
    response = client.delete("/api/admin/delete/user/user@test.com?reason=test")
    assert response.status_code == 403
    assert response.json() == {"detail": "Forbidden"}


@patch("backend.app.routers.admin_panel.get_logs_service", new_callable=AsyncMock)
def test_get_logs_by_admin(mock_get_logs_service, admin_user):
    app.dependency_overrides[get_current_user] = override_get_current_user_admin
    mock_get_logs_service.return_value = {"logs": []}

    response = client.get("/api/admin/logs")
    assert response.status_code == 200
    assert response.json() == {"logs": []}
    mock_get_logs_service.assert_called_once_with(1, 10)


def test_get_logs_by_normal_user(normal_user):
    app.dependency_overrides[get_current_user] = override_get_current_user_normal
    response = client.get("/api/admin/logs")
    assert response.status_code == 403
    assert response.json() == {"detail": "Forbidden"}


@patch("backend.app.routers.admin_panel.delete_deck_service", new_callable=AsyncMock)
def test_delete_deck_by_admin(mock_delete_deck_service, admin_user):
    app.dependency_overrides[get_current_user] = override_get_current_user_admin
    mock_delete_deck_service.return_value = {"message": "Deck deck_id deleted."}

    response = client.delete("/api/admin/delete/deck/deck_id?reason=test")
    assert response.status_code == 200
    assert response.json() == {"message": "Deck deck_id deleted."}
    mock_delete_deck_service.assert_called_once_with(
        "deck_id", "test", "admin@test.com"
    )


@patch("backend.app.routers.admin_panel.add_admin_service", new_callable=AsyncMock)
def test_add_admin_by_admin(mock_add_admin_service, admin_user):
    app.dependency_overrides[get_current_user] = override_get_current_user_admin
    mock_add_admin_service.return_value = {
        "message": "User user@test.com is now admin."
    }

    response = client.put("/api/admin/add/user@test.com")
    assert response.status_code == 200
    assert response.json() == {"message": "User user@test.com is now admin."}
    mock_add_admin_service.assert_called_once_with("user@test.com", "admin@test.com")


@patch("backend.app.routers.admin_panel.remove_admin_service", new_callable=AsyncMock)
def test_remove_admin_by_admin(mock_remove_admin_service, admin_user):
    app.dependency_overrides[get_current_user] = override_get_current_user_admin
    mock_remove_admin_service.return_value = {
        "message": "User user@test.com is no more admin."
    }

    response = client.put("/api/admin/remove/user@test.com")
    assert response.status_code == 200
    assert response.json() == {"message": "User user@test.com is no more admin."}
    mock_remove_admin_service.assert_called_once_with("user@test.com", "admin@test.com")


@patch("backend.app.routers.admin_panel.delete_tag_service", new_callable=AsyncMock)
def test_delete_tag_by_admin(mock_delete_tag_service, admin_user):
    app.dependency_overrides[get_current_user] = override_get_current_user_admin
    mock_delete_tag_service.return_value = {"message": "Tag test_tag deleted."}

    response = client.delete("/api/admin/delete/tag/test_tag?reason=test")
    assert response.status_code == 200
    assert response.json() == {"message": "Tag test_tag deleted."}
    mock_delete_tag_service.assert_called_once_with(
        "test_tag", "test", "admin@test.com"
    )


@patch("backend.app.routers.admin_panel.clear_logs_service", new_callable=AsyncMock)
def test_clear_logs_by_admin(mock_clear_logs_service, admin_user):
    app.dependency_overrides[get_current_user] = override_get_current_user_admin
    mock_clear_logs_service.return_value = {"message": "Logs cleared."}

    response = client.delete("/api/admin/clear/logs")
    assert response.status_code == 200
    assert response.json() == {"message": "Logs cleared."}
    mock_clear_logs_service.assert_called_once_with("admin@test.com")


@pytest.fixture(autouse=True)
def cleanup():
    yield
    app.dependency_overrides = {}
