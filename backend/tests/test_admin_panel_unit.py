import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from backend.app.main import app
from backend.app.services.auth_service import get_current_user

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

@patch("backend.app.services.admin_service.delete_user_service", new_callable=AsyncMock)
def test_delete_user_by_admin(mock_delete_user_service, admin_user):
    app.dependency_overrides[get_current_user] = override_get_current_user_admin
    mock_delete_user_service.return_value = {"message": "User user@test.com deleted."}

    response = client.delete("/api/admin/delete/user/user@test.com?reason=test")
    assert response.status_code == 200
    assert response.json() == {"message": "User user@test.com deleted."}
    mock_delete_user_service.assert_called_once_with("user@test.com", "test", "admin@test.com")

def test_delete_user_by_normal_user(normal_user):
    app.dependency_overrides[get_current_user] = override_get_current_user_normal
    response = client.delete("/api/admin/delete/user/user@test.com?reason=test")
    assert response.status_code == 403
    assert response.json() == {"detail": "Forbidden"}

@patch("backend.app.services.admin_service.get_logs_service", new_callable=AsyncMock)
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

@patch("backend.app.services.admin_service.delete_deck_service", new_callable=AsyncMock)
def test_delete_deck_by_admin(mock_delete_deck_service, admin_user):
    app.dependency_overrides[get_current_user] = override_get_current_user_admin
    mock_delete_deck_service.return_value = {"message": "Deck deck_id deleted."}

    response = client.delete("/api/admin/delete/deck/deck_id?reason=test")
    assert response.status_code == 200
    assert response.json() == {"message": "Deck deck_id deleted."}
    mock_delete_deck_service.assert_called_once_with("deck_id", "test", "admin@test.com")

@patch("backend.app.services.admin_service.add_admin_service", new_callable=AsyncMock)
def test_add_admin_by_admin(mock_add_admin_service, admin_user):
    app.dependency_overrides[get_current_user] = override_get_current_user_admin
    mock_add_admin_service.return_value = {"message": "User user@test.com is now admin."}

    response = client.put("/api/admin/add/user@test.com")
    assert response.status_code == 200
    assert response.json() == {"message": "User user@test.com is now admin."}
    mock_add_admin_service.assert_called_once_with("user@test.com", "admin@test.com")

@patch("backend.app.services.admin_service.remove_admin_service", new_callable=AsyncMock)
def test_remove_admin_by_admin(mock_remove_admin_service, admin_user):
    app.dependency_overrides[get_current_user] = override_get_current_user_admin
    mock_remove_admin_service.return_value = {"message": "User user@test.com is no more admin."}

    response = client.put("/api/admin/remove/user@test.com")
    assert response.status_code == 200
    assert response.json() == {"message": "User user@test.com is no more admin."}
    mock_remove_admin_service.assert_called_once_with("user@test.com", "admin@test.com")

@patch("backend.app.services.admin_service.delete_tag_service", new_callable=AsyncMock)
def test_delete_tag_by_admin(mock_delete_tag_service, admin_user):
    app.dependency_overrides[get_current_user] = override_get_current_user_admin
    mock_delete_tag_service.return_value = {"message": "Tag test_tag deleted."}

    response = client.delete("/api/admin/delete/tag/test_tag?reason=test")
    assert response.status_code == 200
    assert response.json() == {"message": "Tag test_tag deleted."}
    mock_delete_tag_service.assert_called_once_with("test_tag", "test", "admin@test.com")

@patch("backend.app.services.admin_service.clear_logs_service", new_callable=AsyncMock)
def test_clear_logs_by_admin(mock_clear_logs_service, admin_user):
    app.dependency_overrides[get_current_user] = override_get_current_user_admin
    mock_clear_logs_service.return_value = {"message": "Logs cleared."}

    response = client.delete("/api/admin/clear/logs")
    assert response.status_code == 200
    assert response.json() == {"message": "Logs cleared."}
    mock_clear_logs_service.assert_called_once_with("admin@test.com")

# Reset dependency overrides after tests
@pytest.fixture(autouse=True)
def cleanup():
    yield
    app.dependency_overrides = {}