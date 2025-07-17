import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class AIGameSettings(BaseModel):
    time_for_guessing: int = Field(...)
    word_amount: int = Field(...)


class AIGame(BaseModel):
    id: str | None = Field(None, alias="_id")
    deck: list[str]
    game_state: str = "pending"
    settings: AIGameSettings
    remaining_words: list[str] = []
    current_word: str | None = None
    clues: list[str] = []
    score: int = 0
    expires_at: datetime | None = None


class Team(BaseModel):
    id: str
    name: str
    players: list[str] = Field(default_factory=list)
    remaining_words: list[str] = Field(default_factory=list)
    current_word: str | None = None
    expires_at: datetime | None = None
    current_master: str | None = None
    correct_players: list[str] = Field(default_factory=list)
    state: Literal["pending", "in_progress", "finished"] = "pending"
    scores: dict[str, int] = Field(default_factory=dict)
    player_attempts: dict[str, int] = Field(default_factory=dict)
    current_correct: int = 0


class Game(BaseModel):
    id: str | None = Field(None, alias="_id")
    number_of_teams: int = 1
    teams: dict[str, Team] = Field(default_factory=dict)
    deck: list[str] = Field(default_factory=list)
    words_amount: int | None = None
    time_for_guessing: int = 60
    tries_per_player: int = 0
    right_answers_to_advance: int = 1
    rotate_masters: bool = False
    game_state: Literal["pending", "in_progress", "finished"] = "pending"
    winning_team: str | None = None


class TeamStateForHost(BaseModel):
    id: str
    name: str
    remaining_words_count: int
    current_word: str | None
    expires_at: datetime | None
    current_master: str | None
    state: Literal["pending", "in_progress", "finished"]
    scores: dict[str, int] = Field(default_factory=dict)
    players: list[str] = Field(default_factory=list)
    current_correct: int = 0
    right_answers_to_advance: int = 1


class GameState(BaseModel):
    game_state: Literal["pending", "in_progress", "finished"]
    teams: dict[str, TeamStateForHost] = Field(default_factory=dict)
    winning_team: str | None = None


class PlayerGameState(BaseModel):
    game_state: Literal["pending", "in_progress", "finished"]
    team_id: str
    team_name: str
    expires_at: datetime | None
    remaining_words_count: int
    tries_left: int | None = None
    current_word: str | None = None
    current_master: str | None = None
    team_scores: dict[str, int] = Field(default_factory=dict)
    all_teams_scores: dict[str, int] = Field(default_factory=dict)
    players_in_team: list[str] = Field(default_factory=list)
    winning_team: str | None = None


class Deck(BaseModel):
    id: str | None = Field(None, alias="_id")
    name: str = Field(max_length=20)
    words: list[str] = Field(default_factory=list)
    owner_ids: list[str] = Field(default_factory=list)
    tags: list[str] | None = None
    private: bool | None = False


class DeckPreview(BaseModel):
    id: str
    name: str
    words_count: int
    tags: list[str] | None = None
    private: bool | None = False


class DeckDetail(DeckPreview):
    words: list[str]


class DeckIn(BaseModel):
    deck_name: str
    words: list[str]
    tags: list[str] | None = None
    private: bool | None = False


class DeckUpdate(BaseModel):
    deck_name: str | None = None
    words: list[str] | None = None
    tags: list[str] | None = None
    private: bool | None = False


class User(BaseModel):
    name: str = Field(...)
    surname: str = Field(...)
    email: str = Field(...)
    password: str = Field(...)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")
        return v


class UserInDB(BaseModel):
    id: str
    name: str
    surname: str
    email: str
    hashed_password: str
    deck_ids: list[str] = Field(default_factory=list)
    isAdmin: bool | None = Field(default=False)  # noqa: N815


class ProfileResponse(BaseModel):
    id: str
    name: str
    surname: str
    email: str
    isAdmin: bool  # noqa: N815
    decks: list[DeckPreview] = Field(default_factory=list)


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
