import json
import uuid
import time
from typing import Optional, Dict
from app.core.redis import get_redis

MATCHMAKING_QUEUE = "queue:matchmaking"
QUEUE_LOCK = "lock:matchmaking"
HEARTBEAT_EXPIRY = 30  # seconds


def decode_redis_value(value):
    """Helper to decode Redis bytes to string."""
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return value


async def heartbeat_user(user_id: int):
    """Update user's heartbeat to show they're still in queue."""
    redis = await get_redis()
    await redis.set(f"heartbeat:{user_id}", int(time.time()), ex=HEARTBEAT_EXPIRY)


async def is_user_alive(user_id: int) -> bool:
    """Check if user is still active (heartbeat exists)."""
    redis = await get_redis()
    heartbeat = await redis.get(f"heartbeat:{user_id}")
    return heartbeat is not None


async def cleanup_dead_users():
    """Remove users from queue who don't have active heartbeats."""
    redis = await get_redis()
    queue_items = await redis.lrange(MATCHMAKING_QUEUE, 0, -1)
    for item in queue_items:
        user_id = decode_redis_value(item)
        if not await is_user_alive(int(user_id)):
            await redis.lrem(MATCHMAKING_QUEUE, 1, user_id)
            await redis.delete(f"user_match:{user_id}")


async def add_to_queue(user_id: int) -> Optional[Dict]:
    """Add user to matchmaking queue and try to find a match."""
    redis = await get_redis()
    user_id_str = str(user_id)
    await heartbeat_user(user_id)
    await cleanup_dead_users()
    old_match = await redis.get(f"user_match:{user_id}")
    if old_match:
        old_match_id = decode_redis_value(old_match)
        await redis.delete(f"user_match:{user_id}")
        await redis.delete(f"game:{old_match_id}")
        await redis.delete(f"ws_conn:{old_match_id}:{user_id}")
    await redis.lrem(MATCHMAKING_QUEUE, 0, user_id_str)
    queue_items = await redis.lrange(MATCHMAKING_QUEUE, 0, -1)
    queue_items_decoded = [decode_redis_value(item) for item in queue_items]
    if user_id_str not in queue_items_decoded:
        await redis.rpush(MATCHMAKING_QUEUE, user_id_str)
    async with redis.pipeline(transaction=True) as pipe:
        try:
            await pipe.watch(MATCHMAKING_QUEUE)
            queue_length = await redis.llen(MATCHMAKING_QUEUE)
            if queue_length >= 2:
                pipe.multi()
                pipe.lpop(MATCHMAKING_QUEUE)
                pipe.lpop(MATCHMAKING_QUEUE)
                results = await pipe.execute()
                if len(results) >= 2 and results[0] and results[1]:
                    player1_id = decode_redis_value(results[0])
                    player2_id = decode_redis_value(results[1])
                    if not await is_user_alive(int(player1_id)):
                        await redis.lpush(MATCHMAKING_QUEUE, player2_id)
                        return None
                    if not await is_user_alive(int(player2_id)):
                        await redis.lpush(MATCHMAKING_QUEUE, player1_id)
                        return None
                    if player1_id == player2_id:
                        await redis.lpush(MATCHMAKING_QUEUE, player1_id)
                        return None
                    match_id = str(uuid.uuid4())
                    match_data = {
                        "p1": player1_id,
                        "p2": player2_id,
                        "status": "active",
                        "created_at": int(time.time()),
                    }
                    await redis.hset(f"match:{match_id}", mapping=match_data)
                    await redis.expire(f"match:{match_id}", 3600)  # 1 hour expiry
                    await redis.set(f"user_match:{player1_id}", match_id, ex=3600)
                    await redis.set(f"user_match:{player2_id}", match_id, ex=3600)
                    if user_id_str == player1_id:
                        return {
                            "matchId": match_id,
                            "opponent": int(player2_id),
                            "role": "goat",
                        }
                    elif user_id_str == player2_id:
                        return {
                            "matchId": match_id,
                            "opponent": int(player1_id),
                            "role": "tiger",
                        }
                    return None
        except Exception as e:
            await pipe.reset()
            print(f"Matchmaking error: {e}")
    return None


async def remove_from_queue(user_id: int):
    """Remove user from matchmaking queue and cleanup."""
    redis = await get_redis()
    user_id_str = str(user_id)
    await redis.lrem(MATCHMAKING_QUEUE, 0, user_id_str)
    user_match = await redis.get(f"user_match:{user_id}")
    if user_match:
        match_id = decode_redis_value(user_match)
        await redis.delete(f"ws_conn:{match_id}:{user_id}")
    await redis.delete(f"user_match:{user_id}")
    await redis.delete(f"heartbeat:{user_id}")


async def get_match_info(match_id: str) -> Optional[Dict]:
    """Get match information from Redis."""
    redis = await get_redis()
    match_data = await redis.hgetall(f"match:{match_id}")
    if not match_data:
        return None
    decoded_data = {}
    for key, value in match_data.items():
        decoded_key = decode_redis_value(key)
        decoded_value = decode_redis_value(value)
        decoded_data[decoded_key] = decoded_value
    return decoded_data


async def cleanup_match(match_id: str):
    """Clean up match data from Redis."""
    redis = await get_redis()
    match_data = await get_match_info(match_id)
    if match_data:
        p1 = match_data.get("p1")
        p2 = match_data.get("p2")
        if p1:
            await redis.delete(f"user_match:{p1}")
            await redis.delete(f"ws_conn:{match_id}:{p1}")
            await redis.delete(f"heartbeat:{p1}")
        if p2:
            await redis.delete(f"user_match:{p2}")
            await redis.delete(f"ws_conn:{match_id}:{p2}")
            await redis.delete(f"heartbeat:{p2}")
    await redis.delete(f"match:{match_id}")
    await redis.delete(f"game:{match_id}")
