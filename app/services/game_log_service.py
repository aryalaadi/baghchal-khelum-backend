from sqlalchemy.orm import Session
from app.db.models.game_log import GameLog
from app.db.models.user import User
from typing import Optional, Dict, Any


def log_game(
    db: Session,
    match_id: str,
    tiger_player_id: int,
    goat_player_id: int,
    winner_id: Optional[int],
    result: str,
    goats_captured: int,
    total_moves: int,
    game_duration_seconds: Optional[int],
    tiger_elo_before: float,
    tiger_elo_after: float,
    goat_elo_before: float,
    goat_elo_after: float,
    moves_history: Optional[Dict[str, Any]] = None
) -> GameLog:
    """Log a completed game and update player stats."""
    
    # Create game log
    game_log = GameLog(
        match_id=match_id,
        tiger_player_id=tiger_player_id,
        goat_player_id=goat_player_id,
        winner_id=winner_id,
        result=result,
        goats_captured=goats_captured,
        total_moves=total_moves,
        game_duration_seconds=game_duration_seconds,
        tiger_elo_before=tiger_elo_before,
        tiger_elo_after=tiger_elo_after,
        goat_elo_before=goat_elo_before,
        goat_elo_after=goat_elo_after,
        moves_history=moves_history
    )
    db.add(game_log)
    
    # Update player stats
    tiger = db.query(User).filter(User.id == tiger_player_id).first()
    goat = db.query(User).filter(User.id == goat_player_id).first()
    
    if tiger and goat:
        # Update games played for both
        tiger.games_played += 1
        goat.games_played += 1
        
        # Update win/loss/draw stats
        if winner_id is None:
            # Draw
            tiger.games_drawn += 1
            goat.games_drawn += 1
        elif winner_id == tiger_player_id:
            # Tiger won
            tiger.games_won += 1
            goat.games_lost += 1
        else:
            # Goat won
            goat.games_won += 1
            tiger.games_lost += 1
        
        # Update total goats captured for tiger player
        tiger.goats_captured_total += goats_captured
    
    db.commit()
    db.refresh(game_log)
    return game_log


def get_game_logs_by_user(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 20
):
    """Get game logs for a specific user."""
    return db.query(GameLog).filter(
        (GameLog.tiger_player_id == user_id) | (GameLog.goat_player_id == user_id)
    ).order_by(GameLog.created_at.desc()).offset(skip).limit(limit).all()


def get_game_log_by_match_id(db: Session, match_id: str) -> Optional[GameLog]:
    """Get game log by match ID."""
    return db.query(GameLog).filter(GameLog.match_id == match_id).first()
