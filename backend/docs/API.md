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

### DELETE `/api/profile/deck/delete/{deck_id}`
Delete a deck owned by the current user.

### GET `/api/profile/me`
Shortcut for `GET /api/profile/{user_id}` using the authenticated user ID.



## Detailed Examples

# Create a game endpoint

#### Endpoint

POST /api/game/create

<http://217.199.253.164/api/game/create>

#### Request example

All parameters of the game can be changed according to the host"s preferences

curl -X POST <http://217.199.253.164/api/game/create> \  
-H "Content-Type: application/json" \  
-d '{  
"remaining_words": ["krambl", "cookie", "emae"],  
"words_amount": 3,  
"tries_per_player": 3,  
"right_answers_to_advance": 2,  
"time_for_guessing": 60,  
"rotate_masters": true  
}"

#### Response example

{  
"id": "AB52AV"  
}

# Find a deck endpoint

#### Endpoint

GET /api/game/deck/{game_id}

[http://217.199.253.164/api/game/deck/{game_id}](http://217.199.253.164/api/game/deck/%7Bgame_id%7D)

#### Request example

{  
"_id": "somegameidblablabla"  
}

#### Response example

{  
"deck": [lfdwrfe, wewref, werfrrewr]  
}

#### Error codes

404 - Game Not Found

# Handle a player endpoint (websocket)

Live request exchange client <-> server

#### Endpoint

ws://217.199.253.164/api/game/player/{game_id}

#### Request client -> server example

{  
"action": "guess",  
"guess": "яблоко"  
}

#### Request server -> client example

{  
"expires_at": "2025-06-19T15:30:00Z",  
"state": "in_progress",  
"remaining_words_count": 5,  
"tries_left": 2,  
"current_master": "HostName",  
"scores": {"Player1": 3}  
}

#### Error codes

1008 - Missing player"s name  
1011 - Game not found

# Handle a game endpoint (websocket)

Lobbys implemented via websocket.

#### To start the game from lobby

{|  
"action": "start"  
}

Live request exchange client <-> server

#### Endpoint

ws://217.199.253.164/api/game/{game_id}

#### Request client -> server example

Use json with action if skip button is used. If no - server automatically process the timer and new word

{  
"action": "skip"  
}

#### Request server -> client example

If no words remainig server changes the game status to **finished**

##### Example

{  
"current_word": null,  
"expires_at": null,  
"remaining_words_count": 0,  
"state": "finished"  
}

##### If some words remaining

{  
"current_word": "python",  
"expires_at": "2025-06-11T12:30:45.000Z", **optionally**  
"remaining_words_count": 2, **optionally**  
"state": "in_progress"  
}

If word is expired server **automatically** update the new word!!

#### Error codes

1011 - Game not found  
1008 - Game already in progress

# Delete a game endpoint

#### Endpoint

DELETE /api/game/delete/{game_id}

[http://217.199.253.164/api/game/delete/{game_id}](http://217.199.253.164/api/game/delete/%7Bgame_id%7D)

#### Request example

{  
"_id": "somegameidblablabla"  
}

#### Response example

{  
"status": "OK",  
}

#### Error codes

404 - Game Not Found

# Get leaderboard endpoint

#### Endpoint

GET /api/game/leaderboard/{game_id}

[http://217.199.253.164/api/game/leaderboard/{game_id}](http://217.199.253.164/api/game/leaderboard/%7Bgame_id%7D)

#### Request example

{  
"_id": "somegameidblablabla"  
}

#### Response example

{  
"scores": {  
"Player1": 3  
}  
}

#### Error codes

404 - Game Not Found

# Register a user endpoint

#### Endpoint

POST /api/auth/register}

<http://217.199.253.164/api/auth/register>

#### Request example

{  
"email": ["user@example.com](mailto:%22user@example.com)",  
"password": "qwerty52"  
}

#### Response example

{  
"access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",  
"token_type": "bearer"  
}

#### Error codes

400 - Email already registered

# Login endpoint

#### Endpoint

POST /api/auth/login}

<http://217.199.253.164/api/auth/login>

#### Request example

{  
"email": ["user@example.com](mailto:%22user@example.com)",  
"password": "qwerty52"  
}

#### Response example

{  
"access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",  
"token_type": "bearer"  
}

#### Error codes

400 - Incorrect email or password