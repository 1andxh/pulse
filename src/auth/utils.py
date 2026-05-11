from src.config import settings
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import logging

JWT_SECRET = settings.jwt_secret
JWT_ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRY = 3600
REFRESH_TOKEN_EXPIRY_DAYS = 7


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(
    user_data: dict,
    expiry: timedelta = timedelta(seconds=ACCESS_TOKEN_EXPIRY),
    refresh: bool = False,
):
    now = datetime.now(timezone.utc)

    payload = {
        "user": user_data,
        "expiry": now + expiry,
        "jti": str(uuid.uuid4()),
        "refresh": refresh,
        "iat": now,
    }

    return jwt.encode(payload=payload, key=JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, key=JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        logging.warning("Token has expired")
        return None
    except jwt.PyJWTError as e:
        logging.exception(e)
        return None
