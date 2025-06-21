from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.routers.auth import router as auth_router
from backend.app.routers.game import router as game_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,  # type: ignore
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(game_router, prefix="/api/game", tags=["game"])
