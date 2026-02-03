from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class UserStats(BaseModel):
    """User game statistics"""
    games_played: int
    games_won: int
    games_lost: int
    games_drawn: int
    goats_captured_total: int
    win_rate: float
    
    class Config:
        from_attributes = True


class UserProfileBase(BaseModel):
    """Basic user profile information"""
    id: int
    username: str
    elo_rating: float
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserProfileDetailed(UserProfileBase):
    """Detailed user profile with stats"""
    stats: UserStats


class UserListItem(BaseModel):
    """Minimal user info for user lists"""
    id: int
    username: str
    elo_rating: float
    
    class Config:
        from_attributes = True


class GameLogResponse(BaseModel):
    """Game log response"""
    id: int
    match_id: str
    tiger_player_id: int
    goat_player_id: int
    winner_id: Optional[int]
    result: str
    goats_captured: int
    total_moves: int
    game_duration_seconds: Optional[int]
    tiger_elo_before: float
    tiger_elo_after: float
    goat_elo_before: float
    goat_elo_after: float
    created_at: datetime
    
    class Config:
        from_attributes = True


class LeaderboardEntry(BaseModel):
    """Leaderboard entry"""
    rank: int
    user_id: int
    username: str
    elo_rating: float
    games_played: int
    games_won: int
    win_rate: float
    
    class Config:
        from_attributes = True
