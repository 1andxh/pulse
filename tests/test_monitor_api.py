import asyncio

import pytest
from sqlalchemy import select

from src.monitor.models import Monitor


@pytest.mark.asyncio
async def test_create_monitor_api(db_session, client):

    response = await client.post(
        "/monitors/",
        json={
            "name": "Test Monitor",
            "url": "https://example.com",
            "check_interval": 10,
        },
    )

    result = await db_session.execute(select(Monitor))
    monitors = result.scalars().all()

    assert len(monitors) == 1
    assert response.status_code == 201

    data = response.json()
    assert data["url"] == "https://example.com"
    assert data["name"] == "Test Monitor"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_monitor_duplicate(db_session, client):
    payload = {
        "name": "Test Monitor",
        "url": "https://example.com",
        "check_interval": 10,
    }
    response1 = await client.post("/monitors/", json=payload)
    assert response1.status_code == 201

    response2 = await client.post("/monitors/", json=payload)
    assert response2.status_code == 409


@pytest.mark.asyncio
async def test_create_monitor_race_condition(db_session, client):
    payload = {
        "name": "Test-race-Monitor",
        "url": "https://example-race.com",
        "check_interval": 30,
    }

    async def send_request():
        return await client.post("/monitors/", json=payload)

    await asyncio.gather(send_request(), send_request(), return_exceptions=True)

    result = await db_session.execute(select(Monitor))
    monitors = result.scalars().all()

    assert len(monitors) == 1


@pytest.mark.asyncio
async def test_create_monitor_invalid_url(client):
    response = await client.post(
        "/monitors/",
        json={
            "name": "Test Monitor",
            "url": "http://example.com",
            "check_interval": 10,
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_monitors(client):
    await client.post(
        "/monitors/",
        json={
            "name": "Test Monitor",
            "url": "https://example.com",
            "check_interval": 10,
        },
    )

    response = await client.get("/monitors/")
    assert response.status_code == 200
    assert len(response.json()) == 1
