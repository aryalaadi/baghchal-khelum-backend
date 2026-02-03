from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.db.models.user import User
from app.db.models.game_log import GameLog
from app.schemas.user import (
    UserProfileBase,
    UserProfileDetailed,
    UserStats,
    UserListItem,
    GameLogResponse
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/all", response_model=List[UserListItem])
def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get list of all users with pagination."""
    users = db.query(User).order_by(User.elo_rating.desc()).offset(skip).limit(limit).all()
    return users


@router.get("/{user_id}", response_model=UserProfileDetailed)
def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    """Get detailed user profile with stats."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Calculate win rate
    win_rate = (user.games_won / user.games_played * 100) if user.games_played > 0 else 0.0
    
    stats = UserStats(
        games_played=user.games_played,
        games_won=user.games_won,
        games_lost=user.games_lost,
        games_drawn=user.games_drawn,
        goats_captured_total=user.goats_captured_total,
        win_rate=round(win_rate, 2)
    )
    
    return UserProfileDetailed(
        id=user.id,
        username=user.username,
        elo_rating=user.elo_rating,
        created_at=user.created_at,
        stats=stats
    )


@router.get("/{user_id}/stats", response_model=UserStats)
def get_user_stats(user_id: int, db: Session = Depends(get_db)):
    """Get user game statistics."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    win_rate = (user.games_won / user.games_played * 100) if user.games_played > 0 else 0.0
    
    return UserStats(
        games_played=user.games_played,
        games_won=user.games_won,
        games_lost=user.games_lost,
        games_drawn=user.games_drawn,
        goats_captured_total=user.goats_captured_total,
        win_rate=round(win_rate, 2)
    )


@router.get("/{user_id}/games", response_model=List[GameLogResponse])
def get_user_game_logs(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get user's game history."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get games where user was either tiger or goat player
    games = db.query(GameLog).filter(
        (GameLog.tiger_player_id == user_id) | (GameLog.goat_player_id == user_id)
    ).order_by(GameLog.created_at.desc()).offset(skip).limit(limit).all()
    
    return games
