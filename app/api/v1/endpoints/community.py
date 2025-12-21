from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import decode_access_token
from app.db.models.community import Post
from app.schemas.community import PostCreate, PostResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List

router = APIRouter(prefix="/community", tags=["community"])
security = HTTPBearer()

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> int:
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    user_id = int(payload.get("sub"))
    return user_id

@router.post("/post", response_model=PostResponse)
def create_post(post: PostCreate, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """Create a new community post."""
    db_post = Post(
        user_id=user_id,
        title=post.title,
        content=post.content
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

@router.get("/feed", response_model=List[PostResponse])
def get_feed(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """Get community feed."""
    posts = db.query(Post).order_by(Post.created_at.desc()).offset(skip).limit(limit).all()
    return posts
