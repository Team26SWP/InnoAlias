from datetime import datetime
from typing import Optional, List, Literal, Dict
from pydantic import BaseModel, Field


class Game(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    remaining_words: List[str]
    current_word: Optional[str] = None
    expires_at: Optional[datetime] = None
    state: Literal["pending", "in_progress", "finished"] = "pending"
    scores: Dict[str, int] = Field(default_factory=dict)


class GameState(BaseModel):
    current_word: Optional[str]
    expires_at: Optional[datetime]
    remaining_words_count: int
    state: Literal["pending", "in_progress", "finished"]
    scores: Dict[str, int] = Field(default_factory=dict)


class PlayerGameState(BaseModel):
    expires_at: Optional[datetime]
    remaining_words_count: int
    state: Literal["pending", "in_progress", "finished"]
    scores: Dict[str, int] = Field(default_factory=dict)


class User(BaseModel):
    email: str = Field(...)
    password: str = Field(...)


class Token(BaseModel):
    access_token: str
    token_type: str


class UserInDB(BaseModel):
    email: str
    hashed_password: str
