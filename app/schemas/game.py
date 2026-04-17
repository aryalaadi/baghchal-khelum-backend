from pydantic import BaseModel
from typing import Optional, List


class PlaceMove(BaseModel):
    type: str = "place"
    position: int


class MoveAction(BaseModel):
    type: str = "move"
    from_pos: int = None
    to: int

    class Config:
        fields = {"from_pos": "from"}


class GameStart(BaseModel):
    type: str = "start"
    board: List[int]
    turn: str
    phase: int
    role: str
    goats_placed: int
    goats_captured: int


class GameUpdate(BaseModel):
    type: str = "update"
    board: List[int]
    turn: str
    phase: int
    move: dict
    goats_placed: int
    goats_captured: int


class GameOver(BaseModel):
    type: str = "game_over"
    winner: str
    reason: str
    final_board: List[int]


class ErrorMessage(BaseModel):
    type: str = "error"
    message: str


class AIMoveRequest(BaseModel):
    board: List[int]
    turn: str
    phase: int
    goats_placed: int
    goats_captured: int
    ai_role: Optional[str] = None
    mode: str = "hybrid"
    top_k: int = 3


class AIMoveResponse(BaseModel):
    move_type: str
    role: str
    position: Optional[int] = None
    from_pos: Optional[int] = None
    to_pos: Optional[int] = None
    mode_used: str
    score: float
