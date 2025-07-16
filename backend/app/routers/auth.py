from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from backend.app.models import Token, User
from backend.app.services.auth_service import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    create_user,
    get_user,
    verify_refresh_token,
)

router = APIRouter(prefix="", tags=["auth"])


@router.post("/register", response_model=Token)
async def register(user: User):
    """
    Registers a new user in the system.

    Args:
        user (User): The user registration data,
        including name, surname, email, and password.

    Raises:
        HTTPException: 400 if a user with the provided email already exists.

    Returns:
        Token: An object containing the newly generated access and refresh tokens.
    """
    # Check if a user with the given email already exists to prevent duplicate registrations.
    existing_user = await get_user(user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create the new user in the database.
    await create_user(user)

    # Generate access and refresh tokens for the newly registered user.
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
    Authenticates a user based on provided email (username) and password.
    If authentication is successful, returns new access and refresh tokens.

    Args:
        data (OAuth2PasswordRequestForm): Form data containing the username (email) and password.

    Raises:
        HTTPException: 400 if the email or password is incorrect.

    Returns:
        Token: An object containing the new access and refresh tokens.
    """
    # Authenticate the user using the provided credentials.
    user = await authenticate_user(data.username, data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    # Generate access and refresh tokens for the authenticated user.
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
    Refreshes an expired access token using a valid refresh token.
    A new access token and a new refresh token are issued upon successful refresh.

    Args:
        refresh_token (str): The refresh token provided in the request body.

    Returns:
        Token: An object containing the new access and refresh tokens.
    """
    # Verify the refresh token and retrieve the associated user.
    user = await verify_refresh_token(refresh_token)

    # Generate new access and refresh tokens.
    new_access = create_access_token(data={"sub": user.email})
    new_refresh = create_refresh_token(data={"sub": user.email})

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
    }
