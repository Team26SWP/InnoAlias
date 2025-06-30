from datetime import datetime
from typing import Optional, List, Literal, Dict
from pydantic import BaseModel, Field


class Game(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    remaining_words: List[str]
    deck: List[str] = Field(default_factory=list)
    words_amount: Optional[int] = None
    current_word: Optional[str] = None
    expires_at: Optional[datetime] = None
    time_for_guessing: int = 60
    tries_per_player: int = 0
    right_answers_to_advance: int = 1
    rotate_masters: bool = False
    current_master: Optional[str] = None
    correct_players: List[str] = Field(default_factory=list)
    state: Literal["pending", "in_progress", "finished"] = "pending"
    scores: Dict[str, int] = Field(default_factory=dict)


class GameState(BaseModel):
    current_word: Optional[str]
    expires_at: Optional[datetime]
    remaining_words_count: int
    current_correct: int = 0
    right_answers_to_advance: int = 1
    current_master: Optional[str] = None
    state: Literal["pending", "in_progress", "finished"]
    scores: Dict[str, int] = Field(default_factory=dict)
    players: List[str] = Field(default_factory=list)


class PlayerGameState(BaseModel):
    expires_at: Optional[datetime]
    remaining_words_count: int
    tries_left: Optional[int] = None
    current_word: Optional[str] = None
    current_master: Optional[str] = None
    state: Literal["pending", "in_progress", "finished"]
    scores: Dict[str, int] = Field(default_factory=dict)
    players: List[str] = Field(default_factory=list)


class Deck(BaseModel):
    id: str
    name: str = Field(max_length=20)
    words: List[str] = Field(default_factory=list)
    owner_ids: List[str] = Field(default_factory=list)
    tags: Optional[List[str]] = None


class DeckPreview(BaseModel):
    id: str
    name: str
    words_count: int
    tags: Optional[List[str]] = None


class DeckDetail(DeckPreview):
    words: List[str]


class DeckIn(BaseModel):
    deck_name: str
    words: List[str]
    tags: Optional[List[str]] = None


class DeckUpdate(BaseModel):
    deck_name: Optional[str] = None
    words: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class User(BaseModel):
    name: str = Field(...)
    surname: str = Field(...)
    email: str = Field(...)
    password: str = Field(...)


class UserInDB(BaseModel):
    id: str
    name: str
    surname: str
    email: str
    hashed_password: str
    deck_ids: List[str] = Field(default_factory=list)


class ProfileResponse(BaseModel):
    id: str
    name: str
    surname: str
    email: str
    decks: List[DeckPreview] = Field(default_factory=list)


class Token(BaseModel):
    access_token: str
    token_type: str
