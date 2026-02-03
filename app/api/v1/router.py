from fastapi import APIRouter
from app.api.v1.endpoints import auth, matchmaking, game, replay, community, user, friend

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(matchmaking.router)
api_router.include_router(game.router)
api_router.include_router(replay.router)
api_router.include_router(community.router)
api_router.include_router(user.router)
api_router.include_router(friend.router)
