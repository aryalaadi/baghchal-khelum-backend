from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FriendAdd(BaseModel):
    """Request to add a friend"""
    friend_id: int


class FriendResponse(BaseModel):
    """Friend information"""
    id: int
    username: str
    elo_rating: float
    
    class Config:
        from_attributes = True


class ChallengeCreate(BaseModel):
    """Request to challenge a friend"""
    friend_id: int


class ChallengeResponse(BaseModel):
    """Challenge information"""
    id: int
    challenger_id: int
    challenged_id: int
    status: str
    match_id: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChallengeAction(BaseModel):
    """Accept or decline a challenge"""
    challenge_id: int
    action: str  # 'accept' or 'decline'
