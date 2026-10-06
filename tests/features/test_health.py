import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_healthz_ok(client: AsyncClient) -> None:
    """TC-101-1: /healthz return 200 dengan payload benar."""
    resp = await client.get("/api/v1/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "healthy", "version": "1.0.0"}
    assert "x-request-id" in resp.headers


@pytest.mark.asyncio
async def test_readyz_returns_response(client: AsyncClient) -> None:
    """AC-4: /readyz return 200 atau 503 tergantung DB."""
    resp = await client.get("/api/v1/readyz")
    assert resp.status_code in (200, 503)
    body = resp.json()
    if resp.status_code == 200:
        assert body == {"status": "ready", "database": "up"}
    else:
        assert body["error"]["code"] == "DATABASE_ERROR"