import pytest

from src.users.schemas import GoogleUser
from src.users.service import oauth_service


def test_google_user_accepts_openid_subject():
    google_user = GoogleUser(
        sub="google-user-id",
        email="test@example.com",
        name="Test User",
    )

    assert google_user.google_sub == "google-user-id"


@pytest.mark.asyncio
async def test_google_oauth_creates_user(db_session):
    google_user = GoogleUser(
        sub="google-user-id",
        email="test@example.com",
        name="Test User",
    )

    user = await oauth_service.handler_google_user(google_user, db_session)

    assert user.google_sub == "google-user-id"
    assert user.email == "test@example.com"
    assert user.name == "Test User"
    assert user.is_verified is True
    assert user.auth_provider == "google"
