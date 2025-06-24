from datetime import timedelta, datetime, timezone
from typing import Optional
from fastapi import HTTPException, Depends, APIRouter, status
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from decouple import config

from InnoAlias.backend.app.code_gen import generate_user_id
from InnoAlias.backend.app.models import User, UserInDB, Token
from InnoAlias.backend.app.db import db

router = APIRouter(prefix="", tags=["auth"])

SECRET_KEY = config("SECRET_KEY")
ALGORITHM = config("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(config("ACCESS_TOKEN_EXPIRE_MINUTES"))

users = db.users

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def create_user(user: User):
    hashed_password = pwd_context.hash(user.password)
    user_id = await generate_user_id()
    user_credentials = {"_id": user_id,"email": user.email, "hashed_password": hashed_password}
    await users.insert_one(user_credentials)
    return user_credentials


async def get_user(email: str) -> Optional[UserInDB]:
    user = await users.find_one({"email": email})
    if user:
        return UserInDB(email=user["email"], hashed_password=user["hashed_password"])
    return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


async def authenticate_user(email: str, password: str) -> Optional[UserInDB]:
    user = await get_user(email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire_delta = expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + expire_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await get_user(email)
    if user is None:
        raise credentials_exception
    return user


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
