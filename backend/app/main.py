from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import TEXT

from backend.app.db import db
from backend.app.routers.admin_panel import router as admin_router
from backend.app.routers.aigame import router as aigame_router
from backend.app.routers.auth import router as auth_router
from backend.app.routers.gallery import router as gallery_router
from backend.app.routers.game import router as game_router
from backend.app.routers.profile import router as profile_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager for application startup and shutdown events.
    During startup, it creates a text index on the 'decks' collection
    for efficient searching.
    """
    # Create a text index on the 'name' and 'tags' fields of the 'decks' collection
    # Enables full-text search.
    await db.decks.create_index([("name", TEXT), ("tags", TEXT)])
    yield


# Initialize the FastAPI application with the defined lifespan context
app = FastAPI(lifespan=lifespan)

# Configure CORS (Cross-Origin Resource Sharing) middleware
# This allows requests from any origin (*) to access the API,
# enabling credentials, and allowing all methods and headers.
app.add_middleware(
    CORSMiddleware,  # type: ignore
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(game_router, prefix="/api/game", tags=["game"])
app.include_router(profile_router, prefix="/api/profile", tags=["profile"])
app.include_router(gallery_router, prefix="/api/gallery", tags=["gallery"])
app.include_router(aigame_router, prefix="/api/aigame", tags=["aigame"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
