from fastapi import APIRouter
from app.api.v1.endpoints import auth, matchmaking, game, replay, community

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router)
api_router.include_router(matchmaking.router)
api_router.include_router(game.router)
api_router.include_router(replay.router)
api_router.include_router(community.router)
