from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from core.redis_client import get_redis, close_redis
from auth.router import router as auth_router
from matchmaking.router import router as matchmaking_router
from game.router_ws import router as game_router
from replay.router import router as replay_router
from community.router import router as community_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await get_redis()
    yield
    # Shutdown
    await close_redis()

app = FastAPI(title="BaghChal Multiplayer Backend", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(matchmaking_router)
app.include_router(game_router)
app.include_router(replay_router)
app.include_router(community_router)

# Mount static files for test UI
try:
    app.mount("/tests", StaticFiles(directory="tests"), name="tests")
except:
    pass

@app.get("/")
def root():
    return {
        "message": "BaghChal Multiplayer Backend API",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/auth",
            "matchmaking": "/matchmaking",
            "game": "/ws/game",
            "replay": "/replay",
            "community": "/community",
            "test_ui": "/tests/static_test_ui.html"
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
