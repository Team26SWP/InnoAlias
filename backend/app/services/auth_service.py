from datetime import timedelta, datetime, timezone
from typing import Optional
from fastapi import HTTPException, Depends, status
from jose import JWTError, jwt, ExpiredSignatureError  # type: ignore

from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext  # type: ignore

from backend.app.code_gen import generate_user_id
from backend.app.config import (
    SECRET_KEY,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
from backend.app.models import User, UserInDB
from backend.app.db import db

users = db.users
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def create_user(user: User):
    """
    Creates a new user in the database with a hashed password and a generated user ID.
    """
    hashed_password = pwd_context.hash(user.password)
    user_id = await generate_user_id()
    user_credentials = {
        "_id": user_id,
        "name": user.name,
        "surname": user.surname,
        "email": user.email,
        "hashed_password": hashed_password,
        "isAdmin": False,
    }
    await users.insert_one(user_credentials)
    return user_credentials


def _create_token(data: dict, expires_delta: timedelta) -> str:
    """
    Helper function to create a JWT token.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates an access token.
    """
    delta = expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return _create_token(data, delta)


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a refresh token.
    """
    delta = expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return _create_token(data, delta)


def _decode_token(token: str, is_refresh_token: bool = False) -> str:
    """
    Decodes a JWT token and returns the subject (email).
    Raises HTTPException for invalid credentials or expired tokens.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    expired_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token has expired" if is_refresh_token else "Signature has expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        return email
    except ExpiredSignatureError:
        raise expired_exception
    except JWTError:
        raise credentials_exception

async def verify_refresh_token(token: str) -> UserInDB:
    """
    Verifies a refresh token and returns the associated user.
    """
    email = _decode_token(token, is_refresh_token=True)
    user = await get_user(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_user(email: str) -> Optional[UserInDB]:
    """
    Retrieves a user from the database by email.
    """
    user = await users.find_one({"email": email})
    if user:
        return UserInDB(
            email=user["email"],
            hashed_password=user["hashed_password"],
            name=user["name"],
            surname=user["surname"],
            id=user["_id"],
            isAdmin=user.get("isAdmin", False),
        )
    return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against a hashed password.
    """
    return pwd_context.verify(plain_password, hashed_password)


async def authenticate_user(email: str, password: str) -> Optional[UserInDB]:
    """
    Authenticates a user by email and password.
    """
    user = await get_user(email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Retrieves the current authenticated user based on the provided token.
    Raises HTTPException 401 if the token is invalid or user not found.
    """
    email = _decode_token(token)
    user = await get_user(email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Could not validate credentials",
                            headers={"WWW-Authenticate": "Bearer"})
    return user
