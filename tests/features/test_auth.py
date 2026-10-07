import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_signup_invalid_email(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/signup",
        json={"email": "not-an-email", "password": "validpass123"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_signup_password_too_short(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/signup",
        json={"email": "test@example.com", "password": "short1"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_signup_password_no_digit(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/signup",
        json={"email": "test@example.com", "password": "onlyletters"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_signup_password_no_letter(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/signup",
        json={"email": "test@example.com", "password": "12345678"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_signup_email_with_emoji(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/signup",
        json={"email": "test😀@example.com", "password": "validpass123"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_signin_missing_body(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/auth/signin", json={})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_signin_invalid_email(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/signin",
        json={"email": "bad-email", "password": "x"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_me_without_auth_header(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "AUTHENTICATION_ERROR"


@pytest.mark.asyncio
async def test_me_invalid_header_format(client: AsyncClient) -> None:
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "NotBearerFormat"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_empty_bearer(client: AsyncClient) -> None:
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer "},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_malformed_jwt(client: AsyncClient) -> None:
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not.a.real.jwt"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_signout_without_auth(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/auth/signout")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_signout_all_without_auth(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/auth/signout-all")
    assert resp.status_code == 401
