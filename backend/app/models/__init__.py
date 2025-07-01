from datetime import datetime
from typing import Optional, List, Literal, Dict
from pydantic import BaseModel, Field


class Team(BaseModel):
    id: str
    name: str
    players: List[str] = Field(default_factory=list)
    remaining_words: List[str] = Field(default_factory=list)
    current_word: Optional[str] = None
    expires_at: Optional[datetime] = None
    current_master: Optional[str] = None
    correct_players: List[str] = Field(default_factory=list)
    state: Literal["pending", "in_progress", "finished"] = "pending"
    scores: Dict[str, int] = Field(default_factory=dict) # Player scores within this team
    player_attempts: Dict[str, int] = Field(default_factory=dict) # Player attempts within this team for current word
    current_correct: int = 0 # Number of players in this team who guessed the current word


class Game(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    host_id: str # New: ID of the host who created the game
    number_of_teams: int = 1 # New: Number of teams in the game
    teams: Dict[str, Team] = Field(default_factory=dict) # New: Dictionary of Team objects
    deck: List[str] = Field(default_factory=list) # Original full deck, before distribution to teams
    words_amount: Optional[int] = None
    time_for_guessing: int = 60
    tries_per_player: int = 0
    right_answers_to_advance: int = 1
    rotate_masters: bool = False
    game_state: Literal["pending", "in_progress", "finished"] = "pending" # Overall game state
    winning_team: Optional[str] = None # New: ID of the winning team


class TeamStateForHost(BaseModel):
    id: str
    name: str
    remaining_words_count: int
    current_word: Optional[str]
    expires_at: Optional[datetime]
    current_master: Optional[str]
    state: Literal["pending", "in_progress", "finished"]
    scores: Dict[str, int] = Field(default_factory=dict) # Player scores within this team
    players: List[str] = Field(default_factory=list)
    current_correct: int = 0
    right_answers_to_advance: int = 1


class GameState(BaseModel): # For Host
    game_state: Literal["pending", "in_progress", "finished"]
    teams: Dict[str, TeamStateForHost] = Field(default_factory=dict)
    winning_team: Optional[str] = None


class PlayerGameState(BaseModel): # For Player
    game_state: Literal["pending", "in_progress", "finished"]
    team_id: str
    team_name: str
    expires_at: Optional[datetime]
    remaining_words_count: int
    tries_left: Optional[int] = None
    current_word: Optional[str] = None
    current_master: Optional[str] = None
    team_scores: Dict[str, int] = Field(default_factory=dict) # Player scores within player's team
    all_teams_scores: Dict[str, int] = Field(default_factory=dict) # Total scores for all teams
    players_in_team: List[str] = Field(default_factory=list)
    winning_team: Optional[str] = None


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
