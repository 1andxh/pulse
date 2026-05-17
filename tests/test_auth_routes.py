from urllib.parse import parse_qs, urlparse

import pytest

from src.config import settings


@pytest.mark.asyncio
async def test_frontend_oauth_callback_fallback_preserves_tokens(client):
    response = await client.get(
        "/auth/callback?access_token=access-token&refresh_token=refresh-token",
        follow_redirects=False,
    )

    assert response.status_code == 307

    location = response.headers["location"]
    parsed_location = urlparse(location)
    parsed_frontend = urlparse(settings.frontend_url)
    query = parse_qs(parsed_location.query)

    assert parsed_location.scheme == parsed_frontend.scheme
    assert parsed_location.netloc == parsed_frontend.netloc
    assert parsed_location.path == "/auth/callback"
    assert query["access_token"] == ["access-token"]
    assert query["refresh_token"] == ["refresh-token"]
