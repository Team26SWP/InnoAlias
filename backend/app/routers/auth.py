from fastapi import HTTPException, Depends, APIRouter, Body
from fastapi.security import OAuth2PasswordRequestForm

from backend.app.models import User, Token
from backend.app.services.auth_service import (
    create_access_token,
    get_user,
    create_user,
    authenticate_user,
    create_refresh_token,
    verify_refresh_token,
)

router = APIRouter(prefix="", tags=["auth"])


@router.post("/register", response_model=Token)
async def register(user: User):
    """
    Registers a new user.
    Raises HTTPException 400 if the email is already registered.
    """
    existing_user = await get_user(user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    await create_user(user)
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/login", response_model=Token)
async def login(data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticates a user and returns access and refresh tokens.
    Raises HTTPException 400 for incorrect email or password.
    """
    user = await authenticate_user(data.username, data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    return {
        "access_token": token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token)
async def refresh(refresh_token: str = Body(..., embed=True)):
    """
    Refreshes an access token using a refresh token.
    """
    user = await verify_refresh_token(refresh_token)
    new_access = create_access_token(data={"sub": user.email})
    new_refresh = create_refresh_token(data={"sub": user.email})
    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
    }
