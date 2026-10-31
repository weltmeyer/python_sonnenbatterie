"""Login and error-path tests against a fake battery (no hardware needed).

Run with: python -m pytest test/test_login_errors.py
"""
import asyncio
import os
import sys
import threading
import time

import aiohttp
import pytest
import requests
from aiohttp import web

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sonnenbatterie.sonnenbatterie import AsyncSonnenBatterie, sonnenbatterie  # noqa: E402

USER = "User"
PASSWORD = "secret"
SALT = "0123456789abcdef_salt"
CHALLENGE = "d43aeb06a6394daa"


class FakeBattery:
    """Speaks the salted (new firmware) login flow and checks the token."""

    def __init__(self):
        self.session_status = 200   # HTTP status for POST /api/session
        self.challenge_delay = 0    # seconds before answering /api/challenge
        self.token_no = 0
        self.requests = []
        self.put_payloads = []

    @property
    def token(self):
        return f"token{self.token_no}"

    def invalidate_token(self):
        """Simulate a battery restart: the current session token is gone."""
        self.token_no += 1

    async def salt(self, request):
        self.requests.append("salt")
        return web.json_response({"salt": SALT})

    async def challenge(self, request):
        self.requests.append("challenge")
        await asyncio.sleep(self.challenge_delay)
        return web.json_response(CHALLENGE)

    async def session(self, request):
        self.requests.append("session")
        if self.session_status != 200:
            return web.Response(status=self.session_status, text="Bad Gateway")
        form = await request.post()
        expected = AsyncSonnenBatterie.create_response_from_values(None, USER, PASSWORD, CHALLENGE, SALT)
        if form.get("user") != USER or form.get("response") != expected:
            return web.Response(status=401, text="wrong credentials")
        if self.token_no == 0:
            self.token_no = 1
        return web.json_response({"authentication_token": self.token})

    def _authorized(self, request):
        return request.headers.get("Auth-Token") == self.token

    async def data(self, request):
        self.requests.append(request.path)
        if not self._authorized(request):
            return web.Response(status=401)
        return web.json_response({"ok": True})

    async def configurations(self, request):
        self.requests.append(f"{request.method} {request.path}")
        if not self._authorized(request):
            return web.Response(status=401)
        if request.method == "PUT":
            payload = await request.json()
            self.put_payloads.append(payload)
            return web.json_response(payload)
        return web.json_response({"EM_OperatingMode": "2", "EM_USOC": "10"})


@pytest.fixture
def battery():
    """Run the fake battery in its own thread/event loop so that both the
    sync (requests) and async (aiohttp) clients can talk to it."""
    fake = FakeBattery()
    loop = asyncio.new_event_loop()
    started = threading.Event()
    state = {}

    async def start():
        app = web.Application()
        app.router.add_get(f"/api/salt/{USER}", fake.salt)
        app.router.add_get("/api/challenge", fake.challenge)
        app.router.add_post("/api/session", fake.session)
        app.router.add_get("/api/battery", fake.data)
        app.router.add_get("/api/v2/status", fake.data)
        app.router.add_get("/api/v2/configurations", fake.configurations)
        app.router.add_put("/api/v2/configurations", fake.configurations)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()
        state["runner"] = runner
        state["port"] = site._server.sockets[0].getsockname()[1]
        started.set()

    thread = threading.Thread(target=lambda: (loop.run_until_complete(start()), loop.run_forever()), daemon=True)
    thread.start()
    started.wait(5)
    fake.address = f"127.0.0.1:{state['port']}"
    yield fake
    asyncio.run_coroutine_threadsafe(state["runner"].cleanup(), loop).result(5)
    loop.call_soon_threadsafe(loop.stop)
    thread.join(5)


def run(coro):
    return asyncio.run(coro)


def acquired_connections(sb):
    return len(sb._session.connector._acquired) if sb._session else 0


# --- async client ---------------------------------------------------------

def test_async_login_reuses_salt_and_shares_token(battery):
    async def go():
        sb = AsyncSonnenBatterie(USER, PASSWORD, battery.address)
        await sb.login()
        try:
            assert sb.token == battery.token
            assert sb.sb2._api_token == sb.token
            # salt probe, challenge, session -- no second salt request
            assert battery.requests == ["salt", "challenge", "session"]
        finally:
            await sb.logout()
    run(go())


@pytest.mark.parametrize("status", [401, 502])
def test_async_login_failure_keeps_status_and_hides_secrets(battery, status):
    battery.session_status = status

    async def go():
        sb = AsyncSonnenBatterie(USER, PASSWORD, battery.address)
        try:
            with pytest.raises(aiohttp.ClientResponseError) as exc:
                await sb.login()
            assert exc.value.status == status
            text = str(exc.value)
            for secret in (SALT, CHALLENGE, PASSWORD):
                assert secret not in text
            assert acquired_connections(sb) == 0
        finally:
            await sb.logout()
    run(go())


def test_async_login_challenge_times_out(battery):
    battery.challenge_delay = 3

    async def go():
        sb = AsyncSonnenBatterie(USER, PASSWORD, battery.address)
        sb._timeout_total = 1
        sb._timeout = sb._set_timeouts()
        start = time.monotonic()
        try:
            with pytest.raises(asyncio.TimeoutError):
                await sb.login()
            assert time.monotonic() - start < 2.5
        finally:
            await sb.logout()
    run(go())


def test_async_relogin_on_401_updates_v2_token(battery):
    async def go():
        sb = AsyncSonnenBatterie(USER, PASSWORD, battery.address)
        try:
            assert await sb.get_battery() == {"ok": True}
            battery.invalidate_token()
            # v1 request: 401 -> re-login -> retry
            assert await sb.get_battery() == {"ok": True}
            # the v2 client must use the renewed token as well
            assert (await sb.sb2.get_status()) == {"ok": True}

            battery.invalidate_token()
            # v2 call through the v1 client: 401 -> re-login -> retry
            assert (await sb.get_configurations())["EM_OperatingMode"] == "2"
            assert acquired_connections(sb) == 0
        finally:
            await sb.logout()
    run(go())


def test_async_put_retry_keeps_payload(battery):
    async def go():
        sb = AsyncSonnenBatterie(USER, PASSWORD, battery.address)
        try:
            await sb.login()
            battery.invalidate_token()
            await sb._put("v2/configurations", {"EM_USOC": "20"})
            assert battery.put_payloads == [{"EM_USOC": "20"}]
        finally:
            await sb.logout()
    run(go())


def test_async_v2_raises_401_without_retry(battery):
    async def go():
        sb = AsyncSonnenBatterie(USER, PASSWORD, battery.address)
        try:
            await sb.login()
            battery.invalidate_token()
            battery.requests.clear()
            with pytest.raises(aiohttp.ClientResponseError) as exc:
                await sb.sb2.get_status()
            assert exc.value.status == 401
            assert battery.requests == ["/api/v2/status"]
        finally:
            await sb.logout()
    run(go())


# --- sync client ----------------------------------------------------------

def test_sync_login_keeps_token(battery):
    sb = sonnenbatterie(USER, PASSWORD, battery.address)
    assert sb.token == battery.token
    assert sb.sb2.api_token == sb.token
    assert sb.get_battery() == {"ok": True}
    battery.invalidate_token()
    assert sb.get_configurations()["EM_OperatingMode"] == "2"


@pytest.mark.parametrize("status", [401, 502])
def test_sync_login_failure_keeps_status_and_hides_secrets(battery, status):
    battery.session_status = status
    with pytest.raises(requests.HTTPError) as exc:
        sonnenbatterie(USER, PASSWORD, battery.address)
    assert exc.value.response.status_code == status
    for secret in (SALT, CHALLENGE, PASSWORD):
        assert secret not in str(exc.value)
