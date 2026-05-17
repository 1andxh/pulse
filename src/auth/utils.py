import logging
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from authlib.integrations.starlette_client import OAuth

from src.config import settings

JWT_SECRET = settings.jwt_secret
JWT_ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRY = 3600
REFRESH_TOKEN_EXPIRY_DAYS = 7


# oauth
oauth = OAuth()

oauth.register(
    name="google",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile",
    },
    jwks_uri="https://www.googleapis.com/oauth2/v3/certs",
)


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
        "exp": now + expiry,
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
