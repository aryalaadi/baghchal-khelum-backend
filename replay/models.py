from sqlalchemy import Column, Integer, String, JSON, DateTime
from sqlalchemy.sql import func
from core.database import Base

class Replay(Base):
    __tablename__ = "replays"
    
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(String, unique=True, index=True)
    player1_id = Column(Integer, nullable=False)
    player2_id = Column(Integer, nullable=False)
    winner_id = Column(Integer)
    moves = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
