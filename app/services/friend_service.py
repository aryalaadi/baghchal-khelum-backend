from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.models.user import User
from app.db.models.friend_challenge import FriendChallenge, ChallengeStatus
from fastapi import HTTPException, status
import uuid


def add_friend(db: Session, user_id: int, friend_id: int) -> bool:
    """Add a friend relationship."""
    if user_id == friend_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add yourself as a friend"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    friend = db.query(User).filter(User.id == friend_id).first()
    
    if not user or not friend:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if already friends
    if friend in user.friends:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already friends"
        )
    
    # Add bidirectional friendship
    user.friends.append(friend)
    db.commit()
    return True


def remove_friend(db: Session, user_id: int, friend_id: int) -> bool:
    """Remove a friend relationship."""
    user = db.query(User).filter(User.id == user_id).first()
    friend = db.query(User).filter(User.id == friend_id).first()
    
    if not user or not friend:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if friend not in user.friends:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not friends"
        )
    
    user.friends.remove(friend)
    db.commit()
    return True


def get_friends(db: Session, user_id: int) -> List[User]:
    """Get all friends of a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user.friends


def create_challenge(db: Session, challenger_id: int, challenged_id: int) -> FriendChallenge:
    """Create a challenge between friends."""
    if challenger_id == challenged_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot challenge yourself"
        )
    
    challenger = db.query(User).filter(User.id == challenger_id).first()
    challenged = db.query(User).filter(User.id == challenged_id).first()
    
    if not challenger or not challenged:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if they are friends
    if challenged not in challenger.friends:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only challenge friends"
        )
    
    # Check for existing pending challenge
    existing = db.query(FriendChallenge).filter(
        FriendChallenge.challenger_id == challenger_id,
        FriendChallenge.challenged_id == challenged_id,
        FriendChallenge.status == ChallengeStatus.PENDING
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Challenge already pending"
        )
    
    challenge = FriendChallenge(
        challenger_id=challenger_id,
        challenged_id=challenged_id,
        status=ChallengeStatus.PENDING
    )
    db.add(challenge)
    db.commit()
    db.refresh(challenge)
    return challenge


def get_pending_challenges(db: Session, user_id: int) -> List[FriendChallenge]:
    """Get all pending challenges for a user (both sent and received)."""
    challenges = db.query(FriendChallenge).filter(
        ((FriendChallenge.challenger_id == user_id) | (FriendChallenge.challenged_id == user_id)),
        FriendChallenge.status == ChallengeStatus.PENDING
    ).all()
    return challenges


def respond_to_challenge(
    db: Session, challenge_id: int, user_id: int, accept: bool
) -> Optional[str]:
    """Respond to a challenge (accept or decline). Returns match_id if accepted."""
    challenge = db.query(FriendChallenge).filter(FriendChallenge.id == challenge_id).first()
    
    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found"
        )
    
    if challenge.challenged_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to respond to this challenge"
        )
    
    if challenge.status != ChallengeStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Challenge is not pending"
        )
    
    if accept:
        # Generate match ID
        match_id = str(uuid.uuid4())
        challenge.status = ChallengeStatus.ACCEPTED
        challenge.match_id = match_id
        db.commit()
        return match_id
    else:
        challenge.status = ChallengeStatus.DECLINED
        db.commit()
        return None


def get_challenge_by_id(db: Session, challenge_id: int) -> Optional[FriendChallenge]:
    """Get a challenge by ID."""
    return db.query(FriendChallenge).filter(FriendChallenge.id == challenge_id).first()
