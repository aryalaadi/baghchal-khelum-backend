from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.core.redis import get_redis, close_redis
from app.core.config import settings
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_redis()
    yield
    await close_redis()


# Disable Swagger/OpenAPI docs in production
app = FastAPI(
    title="BaghChal Multiplayer Backend",
    lifespan=lifespan,
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://schizoid.men",
        "https://baghchal.schizoid.men",
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

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
            "test_ui": "/tests/static_test_ui.html",
        },
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
