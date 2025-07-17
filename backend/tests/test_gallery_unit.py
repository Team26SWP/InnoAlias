from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from backend.app.models import UserInDB
from backend.app.services.gallery_service import (
    get_gallery_service,
    save_deck_from_gallery_service,
)

# Sample data for tests
PUBLIC_DECK_1 = {
    "_id": "deck1",
    "name": "Public Deck 1",
    "owner_ids": ["user_abc"],
    "words": ["word1", "word2"],
    "tags": ["tag1", "tag2"],
    "private": False,
}
PUBLIC_DECK_2 = {
    "_id": "deck2",
    "name": "Another Public Deck",
    "owner_ids": ["user_def"],
    "words": ["word3", "word4"],
    "tags": ["tag2", "tag3"],
    "private": False,
}
PRIVATE_DECK = {
    "_id": "deck3",
    "name": "Private Deck",
    "owner_ids": ["user_xyz"],
    "words": ["word5", "word6"],
    "tags": ["tag4"],
    "private": True,
}

CURRENT_USER = UserInDB(
    id="user123",
    name="Test",
    surname="User",
    email="test@example.com",
    hashed_password="hashed_password",
    deck_ids=[],
)


@pytest.fixture
def mock_gallery_service_decks():
    with patch(
        "backend.app.services.gallery_service.decks", new_callable=AsyncMock
    ) as mock_decks:
        yield mock_decks


@pytest.fixture
def mock_gallery_service_users():
    with patch(
        "backend.app.services.gallery_service.users", new_callable=AsyncMock
    ) as mock_users:
        yield mock_users


@pytest.mark.asyncio
async def test_get_gallery_service_success(mock_gallery_service_decks):
    """Test successful retrieval of public decks."""
    mock_cursor = AsyncMock()
    mock_cursor.to_list.return_value = [
        {
            "decks": [PUBLIC_DECK_2, PUBLIC_DECK_1],
            "total_count": [{"count": 2}],
        }
    ]
    mock_gallery_service_decks.aggregate.return_value = mock_cursor

    result = await get_gallery_service(page=1, search=None)

    assert result["total_decks"] == 2
    assert len(result["gallery"]) == 2
    assert result["gallery"][0].id == PUBLIC_DECK_2["_id"]
    assert result["gallery"][1].id == PUBLIC_DECK_1["_id"]
    mock_gallery_service_decks.aggregate.assert_called_once()


@pytest.mark.asyncio
async def test_get_gallery_service_pagination(mock_gallery_service_decks):
    """Test pagination logic."""
    # Page 1
    mock_cursor_page_1 = AsyncMock()
    mock_cursor_page_1.to_list.return_value = [
        {
            "decks": [PUBLIC_DECK_1] * 10,
            "total_count": [{"count": 20}],
        }
    ]
    mock_gallery_service_decks.aggregate.return_value = mock_cursor_page_1
    result_page_1 = await get_gallery_service(page=1, search=None)
    assert result_page_1["total_decks"] == 20
    assert len(result_page_1["gallery"]) == 10

    # Page 3 (empty)
    mock_cursor_page_3 = AsyncMock()
    mock_cursor_page_3.to_list.return_value = [
        {"decks": [], "total_count": [{"count": 20}]}
    ]
    mock_gallery_service_decks.aggregate.return_value = mock_cursor_page_3
    result_page_3 = await get_gallery_service(page=3, search=None)
    assert result_page_3["total_decks"] == 20
    assert len(result_page_3["gallery"]) == 0


@pytest.mark.asyncio
async def test_get_gallery_service_search(mock_gallery_service_decks):
    """Test search functionality."""
    mock_cursor = AsyncMock()
    mock_cursor.to_list.return_value = [
        {
            "decks": [PUBLIC_DECK_2],
            "total_count": [{"count": 1}],
        }
    ]
    mock_gallery_service_decks.aggregate.return_value = mock_cursor

    result = await get_gallery_service(page=1, search="Another")

    assert result["total_decks"] == 1
    assert len(result["gallery"]) == 1
    assert result["gallery"][0].name == "Another Public Deck"
    # Ensure the query includes the $text search
    call_args = mock_gallery_service_decks.aggregate.call_args[0][0]
    assert "$search" in call_args[0]["$match"]["$text"]


@pytest.mark.asyncio
async def test_get_gallery_service_invalid_page():
    """Test that an invalid page number raises an HTTPException."""
    with pytest.raises(HTTPException) as exc_info:
        await get_gallery_service(page=0, search=None)
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
@patch("backend.app.services.gallery_service.generate_deck_id", new_callable=AsyncMock)
async def test_save_deck_from_gallery_success(
    mock_generate_id, mock_gallery_service_decks, mock_gallery_service_users
):
    """Test successfully saving a public deck."""
    mock_generate_id.return_value = "new_deck_id"
    mock_gallery_service_decks.find_one.return_value = PUBLIC_DECK_1
    mock_gallery_service_users.update_one.return_value = AsyncMock()
    mock_gallery_service_decks.insert_one.return_value = AsyncMock()

    result = await save_deck_from_gallery_service(PUBLIC_DECK_1["_id"], CURRENT_USER)

    assert result == {"saved_deck_id": "new_deck_id"}
    mock_gallery_service_decks.find_one.assert_called_once_with(
        {"_id": PUBLIC_DECK_1["_id"]}
    )
    mock_gallery_service_decks.insert_one.assert_called_once()
    mock_gallery_service_users.update_one.assert_called_once_with(
        {"_id": CURRENT_USER.id}, {"$addToSet": {"deck_ids": "new_deck_id"}}
    )


@pytest.mark.asyncio
async def test_save_deck_from_gallery_not_found(mock_gallery_service_decks):
    """Test saving a deck that does not exist."""
    mock_gallery_service_decks.find_one.return_value = None
    with pytest.raises(HTTPException) as exc_info:
        await save_deck_from_gallery_service("non_existent_deck", CURRENT_USER)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_save_deck_from_gallery_private(mock_gallery_service_decks):
    """Test saving a private deck."""
    mock_gallery_service_decks.find_one.return_value = PRIVATE_DECK
    with pytest.raises(HTTPException) as exc_info:
        await save_deck_from_gallery_service(PRIVATE_DECK["_id"], CURRENT_USER)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_save_deck_from_gallery_already_owned(mock_gallery_service_decks):
    """Test saving a deck the user already owns."""
    deck_already_owned = PUBLIC_DECK_1.copy()
    deck_already_owned["owner_ids"] = [CURRENT_USER.id]
    mock_gallery_service_decks.find_one.return_value = deck_already_owned

    with pytest.raises(HTTPException) as exc_info:
        await save_deck_from_gallery_service(deck_already_owned["_id"], CURRENT_USER)
    assert exc_info.value.status_code == 409
