from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError, jwt  # type: ignore
from passlib.context import CryptContext  # type: ignore

from backend.app.code_gen import generate_user_id
from backend.app.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    REFRESH_TOKEN_EXPIRE_DAYS,
    SECRET_KEY,
)
from backend.app.db import db
from backend.app.models import User, UserInDB

# Access the 'users' collection from the database instance
users = db.users
# Initialize CryptContext for password hashing and verification
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# OAuth2PasswordBearer for handling token-based authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def create_user(user: User):
    """
    Creates a new user in the database.

    Hashes the user's password before storage and generates a unique user ID.

    Args:
        user (User): The user object containing name, surname, email, and plain password.

    Returns:
        dict: A dictionary representing the created user's credentials, including the hashed password and generated ID.
    """
    # Hash the plain password using bcrypt for secure storage.
    hashed_password = pwd_context.hash(user.password)
    # Generate a unique user ID for the new user.
    user_id = await generate_user_id()
    # Prepare the user credentials for insertion into the database.
    user_credentials = {
        "_id": user_id,
        "name": user.name,
        "surname": user.surname,
        "email": user.email,
        "hashed_password": hashed_password,
        "isAdmin": False,  # Default to non-admin user
    }
    # Insert the new user document into the 'users' collection.
    await users.insert_one(user_credentials)
    return user_credentials


def _create_token(data: dict, expires_delta: timedelta) -> str:
    """
    Helper function to create a JSON Web Token (JWT).

    Encodes the provided data with an expiration time and the application's secret key.

    Args:
        data (dict): The payload to encode into the token (e.g., user ID, email).
        expires_delta (timedelta): The duration for which the token will be valid.

    Returns:
        str: The encoded JWT string.
    """
    to_encode = data.copy()
    # Calculate the expiration time by adding the delta to the current UTC time.
    expire = datetime.now(UTC) + expires_delta
    to_encode.update(
        {"exp": expire.timestamp()}
    )  # Add expiration timestamp to the payload
    # Encode the payload using the secret key and specified algorithm.

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Creates an access token with a default or specified expiration time.

    Args:
        data (dict): The payload for the access token.
        expires_delta (Optional[timedelta]): Custom expiration duration. Defaults to ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
        str: The encoded access token.
    """
    # Use default access token expiration if not provided.

    delta = expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return _create_token(data, delta)


def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Creates a refresh token with a default or specified expiration time.

    Args:
        data (dict): The payload for the refresh token.
        expires_delta (Optional[timedelta]): Custom expiration duration. Defaults to REFRESH_TOKEN_EXPIRE_DAYS.

    Returns:
        str: The encoded refresh token.
    """
    # Use default refresh token expiration if not provided.

    delta = expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return _create_token(data, delta)


def _decode_token(token: str, is_refresh_token: bool = False) -> str:
    """
    Decodes a JWT token and extracts the subject (email).

    Handles token expiration and invalid token errors by raising appropriate HTTPExceptions.

    Args:
        token (str): The JWT string to decode.
        is_refresh_token (bool): Flag to indicate if the token is a refresh token, affecting error messages.

    Raises:
        HTTPException: 401 if the token is expired or otherwise invalid.

    Returns:
        str: The email (subject) extracted from the token payload.
    """
    # Define standard exceptions for invalid or expired credentials.

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
        # Decode the token using the secret key and algorithm.
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        # If the subject (email) is missing from the token payload, raise an error.
        if email is None:
            raise credentials_exception
        # Ensure the email is a string before returning.
        assert isinstance(email, str)
        return email
    except ExpiredSignatureError as err:
        # Catch specific error for expired tokens.
        raise expired_exception from err
    except JWTError as err:
        # Catch general JWT errors (e.g., invalid signature, malformed token).
        raise credentials_exception from err


async def verify_refresh_token(token: str) -> UserInDB:
    """
    Verifies a refresh token and retrieves the associated user from the database.

    Args:
        token (str): The refresh token string.

    Raises:
        HTTPException: 401 if the token is invalid or the user associated with it is not found.

    Returns:
        UserInDB: The user object if the refresh token is valid and the user exists.
    """
    # Decode the refresh token to get the user's email.
    email = _decode_token(token, is_refresh_token=True)
    # Retrieve the user from the database using the email.
    user = await get_user(email)
    # If no user is found for the given email, raise an authentication exception.
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_user(email: str) -> UserInDB | None:
    """
    Retrieves a user from the database by their email address.

    Args:
        email (str): The email of the user to retrieve.

    Returns:
        Optional[UserInDB]: The user object if found, otherwise None.
    """
    # Query the 'users' collection for a user with the given email.
    user = await users.find_one({"email": email})
    # If a user is found, construct and return a UserInDB object.
    if user:
        return UserInDB(
            email=user["email"],
            hashed_password=user["hashed_password"],
            name=user["name"],
            surname=user["surname"],
            id=user["_id"],
            isAdmin=user.get(
                "isAdmin", False
            ),  # Default isAdmin to False if not present
        )
    return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain-text password against a hashed password.

    Args:
        plain_password (str): The plain-text password provided by the user.
        hashed_password (str): The hashed password stored in the database.

    Returns:
        bool: True if the plain password matches the hashed password, False otherwise.
    """
    # Use the password context to securely verify the plain password against the hash.
    return pwd_context.verify(plain_password, hashed_password)


async def authenticate_user(email: str, password: str) -> UserInDB | None:
    """
    Authenticates a user by verifying their email and password.

    Args:
        email (str): The user's email address.
        password (str): The user's plain-text password.

    Returns:
        Optional[UserInDB]: The authenticated user object if credentials are valid, otherwise None.
    """
    # Retrieve the user from the database by email.
    user = await get_user(email)
    # If user not found or password does not match, return None.
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Retrieves the current authenticated user based on the provided access token.

    This function is intended to be used as a FastAPI dependency.

    Args:
        token (str): The access token, automatically injected by OAuth2PasswordBearer.

    Raises:
        HTTPException: 401 if the token is invalid, expired, or the user is not found.

    Returns:
        UserInDB: The authenticated user object.
    """
    # Decode the access token to get the user's email.
    email = _decode_token(token)
    # Retrieve the user from the database using the email.
    user = await get_user(email)
    # If no user is found for the given email, raise an authentication exception.
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
