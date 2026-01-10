from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import decode_access_token
from app.services.auth_service import get_user_by_id
from app.services.matchmaking_service import add_to_queue, remove_from_queue
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(prefix="/matchmaking", tags=["matchmaking"])
security = HTTPBearer()


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> int:
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    user_id = int(payload.get("sub"))
    user = get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return user_id


@router.post("/start")
async def start_matchmaking(user_id: int = Depends(get_current_user_id)):
    """Start matchmaking. Returns match info if found, null if queued."""
    from app.services.matchmaking_service import heartbeat_user

    await heartbeat_user(user_id)
    match_result = await add_to_queue(user_id)
    if match_result:
        return match_result
    else:
        return {"status": "queued", "message": "Waiting for opponent"}


@router.post("/cancel")
async def cancel_matchmaking(user_id: int = Depends(get_current_user_id)):
    """Cancel matchmaking."""
    await remove_from_queue(user_id)
    return {"status": "cancelled"}


@router.post("/heartbeat")
async def update_heartbeat(user_id: int = Depends(get_current_user_id)):
    """Update user's heartbeat to stay in queue."""
    from app.services.matchmaking_service import heartbeat_user

    await heartbeat_user(user_id)
    return {"status": "ok"}


@router.get("/status")
async def check_match_status(user_id: int = Depends(get_current_user_id)):
    """Check if a match has been found (for polling)."""
    from app.core.redis import get_redis
    from app.services.matchmaking_service import (
        heartbeat_user,
        is_user_alive,
        decode_redis_value,
        MATCHMAKING_QUEUE,
    )

    redis = await get_redis()
    queue_items = await redis.lrange(MATCHMAKING_QUEUE, 0, -1)
    queue_items_decoded = [decode_redis_value(item) for item in queue_items]
    if str(user_id) in queue_items_decoded:
        await heartbeat_user(user_id)
    user_match_raw = await redis.get(f"user_match:{user_id}")
    if user_match_raw:
        match_id = (
            user_match_raw.decode()
            if isinstance(user_match_raw, bytes)
            else user_match_raw
        )
        match_data = await redis.hgetall(f"match:{match_id}")
        if match_data:
            p1 = match_data.get(b"p1") or match_data.get("p1")
            p2 = match_data.get(b"p2") or match_data.get("p2")
            p1 = p1.decode() if isinstance(p1, bytes) else p1
            p2 = p2.decode() if isinstance(p2, bytes) else p2
            user_id_str = str(user_id)
            if user_id_str == p1:
                return {"matchId": match_id, "opponent": int(p2), "role": "goat"}
            else:
                return {"matchId": match_id, "opponent": int(p1), "role": "tiger"}
        else:
            await redis.delete(f"user_match:{user_id}")
    return {"status": "waiting"}


@router.post("/leave")
async def leave_match(user_id: int = Depends(get_current_user_id)):
    """Leave current match and clean up."""
    from app.core.redis import get_redis
    from app.services.matchmaking_service import cleanup_match, decode_redis_value

    redis = await get_redis()
    user_match = await redis.get(f"user_match:{user_id}")
    if user_match:
        match_id = decode_redis_value(user_match)
        await cleanup_match(match_id)
        return {"status": "left", "message": "Successfully left the match"}
    return {"status": "not_in_match", "message": "No active match found"}
