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
- `200 OK`: Returns an access token upon successful registration.
- `400 Bad Request`: If the email is already registered.

### POST `/api/auth/login`
Authenticates a user and provides an access token.

**Body** (`application/x-www-form-urlencoded`)
- `username`: The user's email address.
- `password`: The user's password.

**Response**
- `200 OK`: Returns an access token.
- `400 Bad Request`: If credentials are incorrect.

---

## Game Setup

### POST `/api/game/create`
Creates a new game session.

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

### GET `/api/game/deck/{game_id}`
Retrieves the original word deck for a given game.

**Response**
- `200 OK`: Returns the list of words.
- `404 Not Found`: If the game does not exist.

### DELETE `/api/game/delete/{game_id}`
Deletes a game.

**Response**
- `200 OK`: Confirms successful deletion.
- `404 Not Found`: If the game does not exist.

---

## Real-time Gameplay (WebSockets)

### Host Connection
`ws://<host>/api/game/{game_id}?id=<host_id>`

The host connects to this endpoint to manage the game.

**Host Actions (Client -> Server)**
- `{"action": "start_game"}`: Starts the game for all teams.
- `{"action": "stop_game"}`: Ends the game immediately.

**Host State (Server -> Client)**
The host receives a `GameState` object, providing a complete overview of all teams.

### Player Connection
`ws://<host>/api/game/player/{game_id}?name=<player_name>&team_id=<team_id>`

Players connect to this endpoint to participate in the game.

**Player Actions (Client -> Server)**
- `{"action": "guess", "guess": "word"}`: Submits a guess for the current word.
- `{"action": "skip"}`: (Game Master only) Skips the current word.
- `{"action": "switch_team", "new_team_id": "team_2"}`: Switches to a different team (only before the game starts).

**Player State (Server -> Client)**
Players receive a `PlayerGameState` object, tailored to their perspective.

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

All profile endpoints require Bearer Token authentication. Provide it in request header: `Authorization: Bearer <access_token>`

### GET `/api/profile/me`
Retrieves the authenticated user's profile along with their saved decks.

**Response**
- `200 OK`: Returns a `ProfileResponse` object containing the user's details
  and a list of deck previews.
- `401 Unauthorized`: If the token is missing or invalid.

### POST `/api/profile/deck/save`
Saves a new word deck to the user's profile.

**Body** (`application/json`)
- `deck_name`: string
- `words`: array of strings
- `tags`: array of strings *(optional)*

**Response**
- `200 OK`: Returns the ID of the newly created deck.
- `404 Not Found`: If the user record cannot be found.
- `401 Unauthorized`: If authentication fails.

### PATCH `/api/profile/deck/{deck_id}/edit`
Updates an existing deck.

**Body** (`application/json`)
- `deck_name`: string *(optional)*
- `words`: array of strings *(optional)*
- `tags`: array of strings *(optional)*

**Response**
- `200 OK`: Returns the updated `DeckDetail`.
- `404 Not Found`: If the deck does not exist.
- `403 Forbidden`: If the deck is not owned by the user.
- `401 Unauthorized`: If authentication fails.

### GET `/api/profile/deck/{deck_id}`
Retrieves full details of a saved deck.

**Response**
- `200 OK`: Returns a `DeckDetail` object.
- `404 Not Found`: If the deck does not exist.

### DELETE `/api/profile/deck/{deck_id}/delete`
Deletes a deck from the user's profile.

**Response**
- `200 OK`: Returns `{"status": "deleted"}` when the deck is removed.
- `404 Not Found`: If the deck does not exist.
- `403 Forbidden`: If the deck is not owned by the user.
- `401 Unauthorized`: If authentication fails.