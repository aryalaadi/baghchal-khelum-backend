from sqlalchemy.orm import Session
from app.db.models.user import User
import math

K_FACTOR = 32


def calculate_expected_score(rating_a: float, rating_b: float) -> float:
    """Calculate expected score for player A against player B."""
    return 1.0 / (1.0 + math.pow(10, (rating_b - rating_a) / 400.0))


def calculate_new_rating(
    current_rating: float, expected_score: float, actual_score: float
) -> float:
    """Calculate new ELO rating.
    Args:
        current_rating: Current ELO rating
        expected_score: Expected score (0-1)
        actual_score: Actual score (1=win, 0=loss, 0.5=draw)
    """
    return current_rating + K_FACTOR * (actual_score - expected_score)


async def update_elo_ratings(
    db: Session, winner_id: int, loser_id: int, is_draw: bool = False
):
    """Update ELO ratings for both players after a game.
    Args:
        db: Database session
        winner_id: ID of winning player
        loser_id: ID of losing player
        is_draw: Whether the game was a draw
    """
    winner = db.query(User).filter(User.id == winner_id).first()
    loser = db.query(User).filter(User.id == loser_id).first()
    if not winner or not loser:
        return
    winner_rating = winner.elo_rating
    loser_rating = loser.elo_rating
    winner_expected = calculate_expected_score(winner_rating, loser_rating)
    loser_expected = calculate_expected_score(loser_rating, winner_rating)
    if is_draw:
        winner_actual = 0.5
        loser_actual = 0.5
    else:
        winner_actual = 1.0
        loser_actual = 0.0
    winner_new_rating = calculate_new_rating(
        winner_rating, winner_expected, winner_actual
    )
    loser_new_rating = calculate_new_rating(loser_rating, loser_expected, loser_actual)
    winner.elo_rating = winner_new_rating
    loser.elo_rating = loser_new_rating
    db.commit()
    return {
        "winner": {
            "old_rating": winner_rating,
            "new_rating": winner_new_rating,
            "change": winner_new_rating - winner_rating,
        },
        "loser": {
            "old_rating": loser_rating,
            "new_rating": loser_new_rating,
            "change": loser_new_rating - loser_rating,
        },
    }
