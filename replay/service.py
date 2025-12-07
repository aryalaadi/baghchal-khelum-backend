from sqlalchemy.orm import Session
from replay.models import Replay
from typing import List

async def save_replay(db: Session, game_id: str, player1_id: int, player2_id: int, winner_id: int, moves: List[dict]):
    """Save game replay to database."""
    replay = Replay(
        game_id=game_id,
        player1_id=player1_id,
        player2_id=player2_id,
        winner_id=winner_id,
        moves=moves
    )
    db.add(replay)
    db.commit()
    db.refresh(replay)
    return replay

def get_replay(db: Session, game_id: str):
    """Get replay by game ID."""
    return db.query(Replay).filter(Replay.game_id == game_id).first()

def get_user_replays(db: Session, user_id: int, limit: int = 10):
    """Get replays for a user."""
    return db.query(Replay).filter(
        (Replay.player1_id == user_id) | (Replay.player2_id == user_id)
    ).order_by(Replay.created_at.desc()).limit(limit).all()
