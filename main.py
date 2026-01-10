from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.core.redis import get_redis, close_redis
from app.api.v1.router import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_redis()
    yield
    await close_redis()

app = FastAPI(title="BaghChal Multiplayer Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

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
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
