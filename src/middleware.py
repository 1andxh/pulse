from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from src.config import settings


def register_middleware(app: FastAPI):
    app.add_middleware(SessionMiddleware, settings.middleware_secret)

    app.add_middleware(
        TrustedHostMiddleware,
        www_redirect=True,
        allowed_hosts=["localhost", "127.0.0.1", "127.0.0.1:6379"],
    )
