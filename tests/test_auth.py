PREFIX = "/api/v1"


async def test_register_and_login_flow(client):

    r = await client.post(
        f"{PREFIX}/auth/register",
        json={"email": "seller@example.com", "password": "supersecret1"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["email"] == "seller@example.com"
    assert body["wb_token_connected"] is False

    r = await client.post(
        f"{PREFIX}/auth/register",
        json={"email": "seller@example.com", "password": "supersecret1"},
    )
    assert r.status_code == 409

    r = await client.post(
        f"{PREFIX}/auth/login",
        data={"username": "seller@example.com", "password": "supersecret1"},
    )
    assert r.status_code == 200, r.text
    tokens = r.json()
    assert tokens["access_token"] and tokens["refresh_token"]

    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    r = await client.get(f"{PREFIX}/users/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["email"] == "seller@example.com"

    r = await client.post(f"{PREFIX}/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 200
    assert r.json()["access_token"]


async def test_login_wrong_password(client):
    await client.post(
        f"{PREFIX}/auth/register",
        json={"email": "a@b.com", "password": "password123"},
    )
    r = await client.post(
        f"{PREFIX}/auth/login",
        data={"username": "a@b.com", "password": "wrongpass1"},
    )
    assert r.status_code == 401


async def test_me_requires_auth(client):
    r = await client.get(f"{PREFIX}/users/me")
    assert r.status_code == 401


async def test_refresh_token_rejected_as_access(client):
    """Refresh-токен не должен приниматься как access."""
    await client.post(
        f"{PREFIX}/auth/register",
        json={"email": "c@d.com", "password": "password123"},
    )
    r = await client.post(
        f"{PREFIX}/auth/login",
        data={"username": "c@d.com", "password": "password123"},
    )
    refresh = r.json()["refresh_token"]
    r = await client.get(f"{PREFIX}/users/me", headers={"Authorization": f"Bearer {refresh}"})
    assert r.status_code == 401
