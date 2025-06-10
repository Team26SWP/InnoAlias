from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class Game(BaseModel):
    remaining_words: List[str]
    current_word: Optional[str] = None
    turn_expires_at: Optional[datetime] = None