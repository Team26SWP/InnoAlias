from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class Game(BaseModel):
    id: str = None
    remaining_words: List[str]
    current_word: Optional[str] = None
    expires_at: Optional[datetime] = None
    state: Literal["pending", "in_progress", "finished"] = "pending"


class GameState(BaseModel):
    current_word: Optional[str]
    expires_at: Optional[datetime]
    remaining_words_count: int
    state: str


class User(BaseModel):
    email: str = Field(...)
    password: str = Field(...)


class Token(BaseModel):
    access_token: str
    token_type: str


class UserInDB(BaseModel):
    email:str
    hashed_password: str
