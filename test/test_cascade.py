"""Unofficial cascade/config endpoints against a fake battery (no hardware needed).

The single battery's responses are real (sonnenBatterie 10, firmware 1.40.5,
user "User"); the cascade master's responses are assumed from how the
battery's web dashboard uses them and still need confirming on a real cascade.

Run with: python -m pytest test/test_cascade.py
"""
import asyncio
import os
import sys
import threading

import aiohttp
import pytest
import requests
from aiohttp import web

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sonnenbatterie.sonnenbatterie import AsyncSonnenBatterie, sonnenbatterie  # noqa: E402
from sonnenbatterie.cascade import CascadeInfo, build_cascade_info, parse_members  # noqa: E402
from sonnenbatterie.const import (  # noqa: E402
    SONNEN_API_PATH_INVERTER_STACKING_STATUS,
    SONNEN_API_PATH_STACKING_PROTECT,
    SONNEN_API_PATH_STACKING_STATUS,
)

USER = "User"
PASSWORD = "secret"
SALT = "0123456789abcdef_salt"
CHALLENGE = "d43aeb06a6394daa"
TOKEN = "token1"
SERIAL = "100000"

SINGLE = {
    "stacking_status": (200, {"role": "none", "data": None, "country": "DE"}),
    "protect": (400, {"error": "not a stack"}),
    "inverter_stacking": (401, {"error": "401 Unauthorized"}),
}
CASCADE_MASTER = {
    "stacking_status": (200, {"role": "master", "data": None, "country": "DE"}),
    "protect": (200, {"master": {"serial": "100001", "protect_active": True},
                      "slaves": [{"serial": 170167, "protect_active": True}]}),
    "inverter_stacking": (401, {"error": "401 Unauthorized"}),
}


class FakeBattery:
    def __init__(self):
        self.responses = dict(SINGLE)
        self.logins = 0

    async def salt(self, request):
        return web.json_response({"salt": SALT})

    async def challenge(self, request):
        return web.json_response(CHALLENGE)

    async def session(self, request):
        form = await request.post()
        expected = AsyncSonnenBatterie.create_response_from_values(None, USER, PASSWORD, CHALLENGE, SALT)
        if form.get("response") != expected:
            return web.json_response({"error": "401 Unauthorized"}, status=401)
        self.logins += 1
        return web.json_response({"authentication_token": TOKEN})

    def _answer(self, request, name):
        if request.headers.get("Auth-Token") != TOKEN:
            return web.json_response({"error": "401 Unauthorized"}, status=401)
        status, body = self.responses[name]
        return web.json_response(body, status=status)

    async def stacking_status(self, request):
        return self._answer(request, "stacking_status")

    async def protect(self, request):
        return self._answer(request, "protect")

    async def inverter_stacking(self, request):
        return self._answer(request, "inverter_stacking")

    async def configs(self, request):
        if request.headers.get("Auth-Token") != TOKEN:
            return web.json_response({"error": "401 Unauthorized"}, status=401)
        configs = {"DE_Ticket_Number": SERIAL, "CN_CascadingRole": "none", "EM_USOC": "5"}
        name = request.match_info.get("name")
        if name:
            return web.json_response({name: configs[name]})
        return web.json_response(configs)


@pytest.fixture
def battery():
    """Fake battery in its own thread/event loop, for the sync and async clients."""
    fake = FakeBattery()
    loop = asyncio.new_event_loop()
    started = threading.Event()
    state = {}

    async def start():
        app = web.Application()
        app.router.add_get(f"/api/salt/{USER}", fake.salt)
        app.router.add_get("/api/challenge", fake.challenge)
        app.router.add_post("/api/session", fake.session)
        app.router.add_get(f"/api/{SONNEN_API_PATH_STACKING_STATUS}", fake.stacking_status)
        app.router.add_get(f"/api/{SONNEN_API_PATH_STACKING_PROTECT}", fake.protect)
        app.router.add_get(f"/api/{SONNEN_API_PATH_INVERTER_STACKING_STATUS}", fake.inverter_stacking)
        app.router.add_get("/api/configs", fake.configs)
        app.router.add_get("/api/configs/{name}", fake.configs)
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


async def async_cascade_info(battery):
    sb = AsyncSonnenBatterie(USER, PASSWORD, battery.address)
    try:
        await sb.login()
        return await sb.get_cascade_info()
    finally:
        await sb.logout()


# --- async client ---------------------------------------------------------

def test_async_single_battery(battery):
    info = run(async_cascade_info(battery))
    assert isinstance(info, CascadeInfo)
    assert info.role == "none" and not info.is_cascade and info.members == []
    # "not a stack" (400) and "role not permitted" (401) count as not available
    assert info.raw[SONNEN_API_PATH_STACKING_PROTECT] is None
    assert info.raw[SONNEN_API_PATH_INVERTER_STACKING_STATUS] is None
    # the role-based 401 must not be mistaken for an expired session
    assert battery.logins == 1


def test_async_cascade_master(battery):
    battery.responses = dict(CASCADE_MASTER)
    info = run(async_cascade_info(battery))
    assert info.role == "master" and info.is_cascade
    assert [(m.role, m.serial) for m in info.members] == [("master", "100001"), ("slave", "170167")]
    assert info.members_source == SONNEN_API_PATH_STACKING_PROTECT
    assert info.members[0].raw["protect_active"] is True
    assert battery.logins == 1


def test_async_unexpected_error_is_raised(battery):
    battery.responses["protect"] = (500, {"error": "boom"})
    with pytest.raises(aiohttp.ClientResponseError) as exc:
        run(async_cascade_info(battery))
    assert exc.value.status == 500


def test_async_serial_number_and_configs(battery):
    async def go():
        sb = AsyncSonnenBatterie(USER, PASSWORD, battery.address)
        try:
            await sb.login()
            return await sb.get_serial_number(), await sb.get_configs()
        finally:
            await sb.logout()
    serial, configs = run(go())
    assert serial == SERIAL and configs["DE_Ticket_Number"] == SERIAL


# --- sync client ----------------------------------------------------------

def test_sync_single_battery_and_cascade_master(battery):
    sb = sonnenbatterie(USER, PASSWORD, battery.address)
    info = sb.get_cascade_info()
    assert info.role == "none" and not info.is_cascade
    battery.responses = dict(CASCADE_MASTER)
    info = sb.get_cascade_info()
    assert info.role == "master" and [m.serial for m in info.members] == ["100001", "170167"]
    assert battery.logins == 1
    assert sb.get_serial_number() == SERIAL


def test_sync_unexpected_error_is_raised(battery):
    battery.responses["protect"] = (500, {"error": "boom"})
    sb = sonnenbatterie(USER, PASSWORD, battery.address)
    with pytest.raises(requests.HTTPError):
        sb.get_cascade_info()


# --- parsing --------------------------------------------------------------

@pytest.mark.parametrize("data, expected", [
    ({"master": {"serial": 1}, "slaves": [{"serial": 2}, {"serial": "3"}]}, [("master", "1"), ("slave", "2"), ("slave", "3")]),
    ({"role": "master", "data": {"master": {"serial": "1"}, "slaves": []}}, [("master", "1")]),
    ({"master": {"name": "no serial"}}, [("master", None)]),
    ({"role": "none", "data": None}, []),
    (None, []),
    ([1, 2], []),
    ({"slaves": "not a list"}, []),
])
def test_parse_members(data, expected):
    assert [(m.role, m.serial) for m in parse_members(data)] == expected


def test_members_from_inverter_status_when_protect_unavailable():
    info = build_cascade_info({
        SONNEN_API_PATH_STACKING_STATUS: {"role": "slave", "data": None},
        SONNEN_API_PATH_STACKING_PROTECT: None,
        SONNEN_API_PATH_INVERTER_STACKING_STATUS: {"master": {"serial": "1"}, "slaves": [{"serial": "2"}]},
    })
    assert info.role == "slave" and info.is_cascade
    assert info.members_source == SONNEN_API_PATH_INVERTER_STACKING_STATUS and len(info.members) == 2


def test_unknown_role_without_stacking_status():
    info = build_cascade_info({SONNEN_API_PATH_STACKING_STATUS: None})
    assert info.role == "unknown" and not info.is_cascade
