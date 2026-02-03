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
