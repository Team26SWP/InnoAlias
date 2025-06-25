# API Reference

This document describes the REST and WebSocket endpoints exposed by the FastAPI backend.

All endpoints are prefixed with `/api`.

## Authentication

### POST `/api/auth/register`
Create a new user.

**Body** (`application/json`)
- `name`: string
- `surname`: string
- `email`: string
- `password`: string

**Response**
```json
{ "access_token": "<token>", "token_type": "bearer" }
```

### POST `/api/auth/login`
Authenticate an existing user.

Send credentials as form data using the standard OAuth2 fields `username` and `password`.

**Response**
```json
{ "access_token": "<token>", "token_type": "bearer" }
```

## Game

### POST `/api/game/create`
Create a new game.

**Body** (`application/json`)
- `remaining_words`: array of strings – list of words to use
- `words_amount`: integer (optional) – limit number of words
- `time_for_guessing`: integer (seconds, default `60`)
- `tries_per_player`: integer (default `0`, unlimited)
- `right_answers_to_advance`: integer (default `1`)
- `rotate_masters`: boolean (default `false`)

**Response**
```json
{ "id": "<game_id>" }
```

### GET `/api/game/leaderboard/{game_id}/export`
Download all words of a game deck as a text file.

### GET `/api/game/{game_id}/deck`
Return the full list of words of a deck.

**Response**
```json
{ "words": ["word1", "word2", ...] }
```

### POST `/api/game/{game_id}/deck/save`
Save a deck to the current user's profile.
Requires an authentication token.

Parameters:
- `deck_name` – string (query)
- `tags` – list of strings (optional, query)

**Body** (`application/json`)
Dictionary of words to save.

**Response**
```json
{ "inserted_id": "<deck_id>" }
```

### DELETE `/api/game/delete/{game_id}`
Remove a game document.

### GET `/api/game/leaderboard/{game_id}`
Return sorted scores for a finished game.

### WebSocket `/api/game/{game_id}`
Host connection for controlling the game.
Optional query parameter `name` sets the host's display name.

### WebSocket `/api/game/player/{game_id}`
Player connection. Use query parameter `name` to specify the player name.
Messages use JSON and depend on the current state of the game.

## Profile

All profile routes require authentication unless stated otherwise.

### GET `/api/profile/{user_id}`
Return user information and list of decks owned by the user.

**Response** (`application/json`)
```json
{
  "id": "<user_id>",
  "name": "...",
  "surname": "...",
  "email": "...",
  "decks": [
    { "id": "<deck_id>", "name": "...", "words_count": 10, "tags": [] }
  ]
}
```

### GET `/api/profile/deck/{deck_id}`
Retrieve details of a specific deck.

**Response**
```json
{
  "id": "<deck_id>",
  "name": "...",
  "words_count": 10,
  "tags": [],
  "words": ["word1", "word2", ...]
}
```

### DELETE `/api/profile/deck/{deck_id}`
Delete a deck owned by the current user.

### GET `/api/profile/me`
Shortcut for `GET /api/profile/{user_id}` using the authenticated user ID.

