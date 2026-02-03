from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.core.redis import get_redis, close_redis
from app.core.config import settings
from app.api.v1.router import api_router
import traceback


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

# CORS origins
origins = [
    "https://schizoid.men",
    "https://baghchal.schizoid.men",
    "http://localhost:3000",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler to ensure CORS headers are always sent
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Unhandled exception: {exc}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
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
