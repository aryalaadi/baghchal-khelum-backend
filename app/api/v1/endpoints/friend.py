from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.api.deps import get_current_user
from app.db.models.user import User
from app.schemas.friend import (
    FriendAdd,
    FriendResponse,
    ChallengeCreate,
    ChallengeResponse,
    ChallengeAction
)
from app.services import friend_service

router = APIRouter(prefix="/friends", tags=["friends"])


@router.post("/add")
def add_friend(
    friend_data: FriendAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a friend."""
    friend_service.add_friend(db, current_user.id, friend_data.friend_id)
    return {"message": "Friend added successfully"}


@router.delete("/{friend_id}")
def remove_friend(
    friend_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a friend."""
    friend_service.remove_friend(db, current_user.id, friend_id)
    return {"message": "Friend removed successfully"}


@router.get("/", response_model=List[FriendResponse])
def get_friends(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of friends."""
    friends = friend_service.get_friends(db, current_user.id)
    return friends


@router.post("/challenge", response_model=ChallengeResponse)
def create_challenge(
    challenge_data: ChallengeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Challenge a friend to a game."""
    challenge = friend_service.create_challenge(
        db, current_user.id, challenge_data.friend_id
    )
    return challenge


@router.get("/challenges", response_model=List[ChallengeResponse])
def get_challenges(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all pending challenges (sent and received)."""
    challenges = friend_service.get_pending_challenges(db, current_user.id)
    return challenges


@router.post("/challenge/respond")
def respond_to_challenge(
    action_data: ChallengeAction,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Accept or decline a challenge."""
    if action_data.action not in ["accept", "decline"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Action must be 'accept' or 'decline'"
        )
    
    accept = action_data.action == "accept"
    match_id = friend_service.respond_to_challenge(
        db, action_data.challenge_id, current_user.id, accept
    )
    
    if accept:
        return {
            "message": "Challenge accepted",
            "match_id": match_id,
            "action": "accepted"
        }
    else:
        return {
            "message": "Challenge declined",
            "action": "declined"
        }
