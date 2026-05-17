from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from src.config import settings


def register_middleware(app: FastAPI):
    app.add_middleware(SessionMiddleware, secret_key=settings.middleware_secret)

    app.add_middleware(
        TrustedHostMiddleware,
        www_redirect=True,
        allowed_hosts=["localhost", "127.0.0.1", settings.redis_url, settings.api_url],
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:5173",
            "http://localhost:5173",
            settings.frontend_url,
        ],
        allow_credentials=False,  # no cookies
        allow_methods=["*"],
        allow_headers=["*"],
    )
