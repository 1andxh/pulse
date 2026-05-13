from src.config import settings
from authlib.integrations.starlette_client import OAuth
from fastapi import Response
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import logging
from .schemas import Token

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


def set_auth_cookies(response: Response, tokens: Token) -> None:
    cookie_config = {
        "httponly": True,
        "samesite": "lax",
        "secure": False,  # nts: always TRUE in prod
    }
    response.set_cookie(
        key="access_token",
        value=tokens.access_token,
        max_age=ACCESS_TOKEN_EXPIRY,
        **cookie_config,
    )
    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        max_age=REFRESH_TOKEN_EXPIRY_DAYS * 24 * 60 * 60,
        **cookie_config,
    )

    # usage -- /callback
    tokens = auth_service.generate_token_pair(user)  # type: ignore

    redirect = RedirectResponse(url=f"{settings.frontend_url}/stats")  # type: ignore
    set_auth_cookies(redirect, tokens)
    # return redirect
