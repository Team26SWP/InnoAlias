# API documentation

This document provides a comprehensive reference for the InnoAlias backend API, including REST endpoints and WebSocket channels for real-time gameplay.

All endpoints are prefixed with `/api`.

Most routes return JSON. For authenticated endpoints, include
`Authorization: Bearer <token>` in the request headers.

---

## Core Game Mechanics

The game revolves around a host who creates and manages a game, and players who join to guess words.

- **Teams**: The game can be played with one or more teams. If there is only one team, all players are on it. When multiple teams are created, players can choose which team to join.
- **Gameplay**: Each team operates as an independent game, with its own deck of words, game master, and timer.
- **Game Master**: A game master is responsible for explaining the current word to their teammates. The game master can be a single, fixed player for the entire game or can rotate among team members after each word, depending on the game settings.
- **Winning**: The game concludes when all teams have exhausted their word decks. The team with the highest score at the end is declared the winner.

---

## Authentication

### POST `/api/auth/register`
Creates a new user account.

**Body** (`application/json`)
- `name`: string
- `surname`: string
- `email`: string (must be unique)
- `password`: string

**Response**
- `200 OK`: Returns an access token and a refresh token upon successful registration.
  ```json
  {
    "access_token": "your_jwt_access_token",
    "refresh_token": "your_jwt_refresh_token",
    "token_type": "bearer"
  }
  ```
- `400 Bad Request`: If the email is already registered.

### POST `/api/auth/login`
Authenticates a user and provides an access token and a refresh token.

**Body** (`application/x-www-form-urlencoded`)
- `username`: The user's email address.
- `password`: The user's password.

**Response**
- `200 OK`: Returns an access token and a refresh token.
  ```json
  {
    "access_token": "your_jwt_access_token",
    "refresh_token": "your_jwt_refresh_token",
    "token_type": "bearer"
  }
  ```
- `400 Bad Request`: If credentials are incorrect.

### POST `/api/auth/refresh`
Refreshes an expired access token using a valid refresh token.

**Body** (`application/json`)
```json
{
  "refresh_token": "your_jwt_refresh_token"
}
```

**Response**
- `200 OK`: Returns a new access token and a new refresh token.
  ```json
  {
    "access_token": "new_jwt_access_token",
    "refresh_token": "new_jwt_refresh_token",
    "token_type": "bearer"
  }
  ```
- `401 Unauthorized`: If the refresh token is invalid, expired, or has been revoked.

---

## Game Setup

### POST `/api/game/create`
Creates a new game session. Requires authentication.

**Body** (`application/json`)
- `host_id`: string - The ID of the user hosting the game.
- `number_of_teams`: integer - The number of teams in the game (e.g., `1` for a free-for-all, `2` or more for team play).
- `deck`: array of strings - The list of words to be used in the game.
- `words_amount`: integer *(optional)* - Limit the number of words taken from the deck.
- `time_for_guessing`: integer (seconds) - The time limit for guessing each word.
- `tries_per_player`: integer - The number of guess attempts per player for each word (0 for unlimited).
- `right_answers_to_advance`: integer - The number of correct guesses required to advance to the next word.
- `rotate_masters`: boolean - If `true`, the game master role rotates among players in a team.

**Response**
- `200 OK`: Returns the unique ID for the newly created game.
  ```json
  { "id": "<game_id>" }
  ```
- `401 Unauthorized`: If authentication fails.

### GET `/api/game/deck/{game_id}`
Retrieves the original word deck for a given game.

**Response**
- `200 OK`: Returns the list of words.
  ```json
  { "words": ["word1", "word2", ...] }
  ```
- `404 Not Found`: If the game does not exist.

### DELETE `/api/game/delete/{game_id}`
Deletes a game. Requires authentication.

**Response**
- `200 OK`: Confirms successful deletion.
  ```json
  { "status": "OK" }
  ```
- `401 Unauthorized`: If authentication fails.
- `404 Not Found`: If the game does not exist.

---

## AI Game

### POST `/api/aigame/create`
Creates a new game session against an AI.

**Body** (`application/json`)
```json
{
  "deck": ["word1", "word2", "word3"],
  "settings": {
    "time_for_guessing": 60,
    "word_amount": 10
  }
}
```

**Response**
- `200 OK`: Returns the unique ID for the newly created AI game.
  ```json
  { "game_id": "<game_id>" }
  ```

---

## Real-time Gameplay (WebSockets)

### Host Connection
`ws://<host>/api/game/{game_id}?id=<host_id>`

The host connects to this endpoint to manage the game. Requires the `host_id` to match the game's host.

**Host Actions (Client -> Server)**
- `{"action": "start_game"}`: Starts the game for all teams.
- `{"action": "stop_game"}`: Ends the game immediately.

**Host State (Server -> Client)**
The host receives a `GameState` object, providing a complete overview of all teams. This is broadcasted whenever the game state changes. The host can always see the unmasked `current_word`.
**Example `GameState` Payload:**
```json
{
  "game_state": "in_progress",
  "teams": {
    "team_1": {
      "id": "team_1",
      "name": "Team 1",
      "remaining_words_count": 9,
      "current_word": "example",
      "expires_at": "2025-12-01T12:00:00Z",
      "current_master": "player1",
      "state": "in_progress",
      "scores": { "player1": 0, "player2": 1 },
      "players": ["player1", "player2"],
      "current_correct": 1,
      "right_answers_to_advance": 1
    }
  },
  "winning_team": null
}
```

### Player Connection
`ws://<host>/api/game/player/{game_id}?name=<player_name>&team_id=<team_id>`

Players connect to this endpoint to participate in the game.

**Player Actions (Client -> Server)**
- `{"action": "guess", "guess": "word"}`: Submits a guess for the current word.
- `{"action": "skip"}`: (Game Master only) Skips the current word.
- `{"action": "switch_team", "new_team_id": "team_2"}`: Switches to a different team (only before the game starts).

**Player State (Server -> Client)**
Players receive a `PlayerGameState` object, tailored to their perspective. This is broadcasted whenever the game state changes. The `current_word` is masked with asterisks for all players except the `current_master`.
**Example `PlayerGameState` Payload:**
```json
{
  "game_state": "in_progress",
  "team_id": "team_1",
  "team_name": "Team 1",
  "expires_at": "2025-12-01T12:00:00Z",
  "remaining_words_count": 9,
  "tries_left": null,
  "current_word": "e******",
  "current_master": "player1",
  "team_scores": { "player1": 0, "player2": 1 },
  "all_teams_scores": { "Team 1": 1, "Team 2": 0 },
  "players_in_team": ["player1", "player2"],
  "winning_team": null
}
```

### AI Game Connection
`ws://<host>/api/aigame/{game_id}`

A player connects to this endpoint to play against the AI.

**Player Actions (Client -> Server)**
- `{"action": "start_game"}`: Starts the game.
- `{"action": "guess", "guess": "word"}`: Submits a guess for the current word.
- `{"action": "skip"}`: Skips the current word.

**Game State (Server -> Client)**
The server broadcasts the game state to the client whenever it changes. The state includes `game_state`, `current_word`, `score`, `clues`, etc.

---

## Leaderboard

### GET `/api/game/leaderboard/{game_id}`
Retrieves the final leaderboard for a game, sorted by team scores.

**Response**
- `200 OK`: Returns a detailed leaderboard with team and player scores.
- `404 Not Found`: If the game does not exist.

### GET `/api/game/leaderboard/{game_id}/export`
Downloads the game's word deck as a `.txt` file.

---

## User Profile & Decks

All profile endpoints require Bearer Token authentication.

### GET `/api/profile/me`
Retrieves the authenticated user's profile along with their saved decks.

**Response**
- `200 OK`: Returns a `ProfileResponse` object.
- `401 Unauthorized`: If the token is missing or invalid.

### GET `/api/profile/{user_id}`
Retrieves a user's profile.

**Response**
- `200 OK`: Returns a `ProfileResponse` object.
- `401 Unauthorized`: If authentication fails.
- `403 Forbidden`: If the user is trying to access another user's profile.
- `404 Not Found`: If the user does not exist.

### POST `/api/profile/deck/save`
Saves a new word deck to the user's profile.

**Body** (`application/json`)
- `deck_name`: string
- `words`: array of strings
- `tags`: array of strings *(optional)*
- `private`: boolean *(optional, defaults to false)*

**Response**
- `200 OK`: Returns the ID of the newly created deck.
  ```json
  { "inserted_id": "<deck_id>" }
  ```
- `401 Unauthorized`: If authentication fails.
- `404 Not Found`: If the user record cannot be found.

### PATCH `/api/profile/deck/{deck_id}/edit`
Updates an existing deck.

**Body** (`application/json`)
- `deck_name`: string *(optional)*
- `words`: array of strings *(optional)*
- `tags`: array of strings *(optional)*
- `private`: boolean *(optional)*

**Response**
- `200 OK`: Returns the updated `DeckDetail`.
- `401 Unauthorized`: If authentication fails.
- `403 Forbidden`: If the deck is not owned by the user.
- `404 Not Found`: If the deck does not exist.

### GET `/api/profile/deck/{deck_id}`
Retrieves full details of a saved deck.

**Response**
- `200 OK`: Returns a `DeckDetail` object, which includes the `private` status.
- `404 Not Found`: If the deck does not exist.

### DELETE `/api/profile/deck/{deck_id}/delete`
Deletes a deck from the user's profile.

**Response**
- `200 OK`: Returns `{"status": "deleted"}`.
- `401 Unauthorized`: If authentication fails.
- `403 Forbidden`: If the deck is not owned by the user.
- `404 Not Found`: If the deck does not exist.

---

## Gallery

### GET `/api/gallery/decks`
Retrieves a paginated list of public decks from the gallery.

**Query Parameters**
- `number`: The page number to retrieve (50 decks per page).

**Response**
- `200 OK`: Returns a list of decks and the total count of public decks.
- `404 Not Found`: If the page number is invalid.

### PUT `/api/gallery/decks/{deck_id}`
Saves a public deck from the gallery to the current user's profile. Requires authentication.

**Response**
- `200 OK`: Returns the ID of the saved deck.
- `401 Unauthorized`: If authentication fails.
- `403 Forbidden`: If the deck is private.
- `404 Not Found`: If the user or deck does not exist, or if the user already has the deck.

---

## Admin Panel

All admin endpoints require an admin user's Bearer Token.

### DELETE `/api/admin/delete/user/{user_id}`
Deletes a user.

**Query Parameters**
- `reason`: The reason for deleting the user.

**Response**
- `200 OK`: Confirms the user has been deleted.
- `401 Unauthorized`: If authentication fails.
- `403 Forbidden`: If the current user is not an admin.
- `404 Not Found`: If the user does not exist.

### GET `/api/admin/logs`
Retrieves all admin action logs.

**Response**
- `200 OK`: Returns a list of logs.
- `401 Unauthorized`: If authentication fails.
- `403 Forbidden`: If the current user is not an admin.
- `404 Not Found`: If there are no logs.

### DELETE `/api/admin/delete/deck/{deck_id}`
Deletes a deck.

**Query Parameters**
- `reason`: The reason for deleting the deck.

**Response**
- `200 OK`: Confirms the deck has been deleted.
- `401 Unauthorized`: If authentication fails.
- `403 Forbidden`: If the current user is not an admin.
- `404 Not Found`: If the deck does not exist.

### PUT `/api/admin/add/{user_id}`
Grants admin privileges to a user.

**Response**
- `200 OK`: Confirms the user is now an admin.
- `401 Unauthorized`: If authentication fails.
- `403 Forbidden`: If the current user is not an admin.
- `404 Not Found`: If the user does not exist.

### PUT `/api/admin/remove/{user_id}`
Revokes admin privileges from a user.

**Response**
- `200 OK`: Confirms the user is no longer an admin.
- `401 Unauthorized`: If authentication fails.
- `403 Forbidden`: If the current user is not an admin.
- `404 Not Found`: If the user does not exist.

### DELETE `/api/admin/delete/tag/{tag}`
Deletes a tag from all decks.

**Query Parameters**
- `reason`: The reason for deleting the tag.

**Response**
- `200 OK`: Confirms the tag has been deleted.
- `401 Unauthorized`: If authentication fails.
- `403 Forbidden`: If the current user is not an admin.

### DELETE `/api/admin/clear/logs`
Clears all admin action logs.

**Response**
- `200 OK`: Confirms the logs have been cleared.
- `401 Unauthorized`: If authentication fails.
- `403 Forbidden`: If the current user is not an admin.