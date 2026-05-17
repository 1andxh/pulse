from urllib.parse import urlparse

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from src.config import settings


def _host_from_url(value: str) -> str:
    parsed = urlparse(value)
    return parsed.netloc or parsed.path


def register_middleware(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:5173",
            "http://localhost:5173",
            settings.frontend_url,
        ],
        allow_credentials=True,  # no cookies
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", _host_from_url(settings.api_url)],
    )

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.middleware_secret,
        session_cookie="session",
        same_site="lax",
        https_only=False,
        max_age=300,
    )
