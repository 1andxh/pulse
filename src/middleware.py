from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.cors import CORSMiddleware
from src.config import settings


def register_middleware(app: FastAPI):
    app.add_middleware(SessionMiddleware, settings.middleware_secret)

    app.add_middleware(
        TrustedHostMiddleware,
        www_redirect=True,
        allowed_hosts=["localhost", "127.0.0.1", "127.0.0.1:6379", settings.api_url],
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
