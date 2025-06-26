from fastapi import HTTPException, Depends, APIRouter
from fastapi.security import OAuth2PasswordRequestForm

from backend.app.models import User, Token
from backend.app.services.auth_service import (
    create_access_token,
    get_user,
    create_user,
    authenticate_user,
)

router = APIRouter(prefix="", tags=["auth"])



@router.post("/register", response_model=Token)
async def register(user: User):
    existing_user = await get_user(user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    await create_user(user)
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
async def login(data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(data.username, data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    token = create_access_token(data={"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}
