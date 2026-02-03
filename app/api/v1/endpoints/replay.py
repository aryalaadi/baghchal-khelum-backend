from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.replay_service import get_replay, get_user_replays

router = APIRouter(prefix="/replay", tags=["replay"])


@router.get("/{game_id}")
def get_game_replay(game_id: str, db: Session = Depends(get_db)):
    """Get replay for a specific game."""
    replay = get_replay(db, game_id)
    if not replay:
        raise HTTPException(status_code=404, detail="Replay not found")
    return {
        "game_id": replay.game_id,
        "player1_id": replay.player1_id,
        "player2_id": replay.player2_id,
        "winner_id": replay.winner_id,
        "moves": replay.moves,
        "created_at": replay.created_at,
    }


@router.get("/user/{user_id}")
def get_user_game_replays(user_id: int, limit: int = 10, db: Session = Depends(get_db)):
    """Get replays for a specific user."""
    replays = get_user_replays(db, user_id, limit)
    return [
        {
            "game_id": replay.game_id,
            "player1_id": replay.player1_id,
            "player2_id": replay.player2_id,
            "winner_id": replay.winner_id,
            "created_at": replay.created_at,
        }
        for replay in replays
    ]
