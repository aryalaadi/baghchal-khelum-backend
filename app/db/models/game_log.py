from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.db.session import Base


class GameLog(Base):
    __tablename__ = "game_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(String, index=True, nullable=False)
    
    # Players
    tiger_player_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    goat_player_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Game outcome
    winner_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # None for draw
    result = Column(String, nullable=False)  # 'tiger_win', 'goat_win', 'draw'
    
    # Game stats
    goats_captured = Column(Integer, default=0)
    total_moves = Column(Integer, default=0)
    game_duration_seconds = Column(Integer, nullable=True)
    
    # ELO changes
    tiger_elo_before = Column(Float, nullable=False)
    tiger_elo_after = Column(Float, nullable=False)
    goat_elo_before = Column(Float, nullable=False)
    goat_elo_after = Column(Float, nullable=False)
    
    # Game data (optional - store moves history)
    moves_history = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
