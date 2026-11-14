"""Unofficial cascade/config endpoints against a fake battery (no hardware needed).

All responses are real (sonnenBatterie 10, firmware 1.40.5; serials and IPs
replaced): a single battery; the master and a slave of a two-unit cascade
with user "User"; the master and a slave of a three-unit cascade with user
"Installer".

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
from sonnenbatterie.cascade import CASCADE_ENDPOINTS, CascadeInfo, build_cascade_info, parse_members  # noqa: E402
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
    "stacking_status": (200, {"country": "BE", "role": "master", "data": {
        "master": {"100001": {"ip": "192.0.2.51", "status": "WORKING"}},
        "slaves": {"100002": {"ip": "192.0.2.114", "status": "WORKING"}},
    }}),
    "protect": (200, {"master": {"backup_buffer": 0, "protect_active": False, "serial": "100001"},
                      "slaves": [{"backup_buffer": 0, "protect_active": False, "serial": "100002"}]}),
    "inverter_stacking": (401, {"error": "401 Unauthorized"}),
}


# Installer may read the inverter stacking status
_INVERTER = {"grid_code_status": "set", "installed_version1": "3.18.0",
             "installed_version2": "4.7.14", "inverter_grid_code": "4901"}
CASCADE_MASTER_INSTALLER = {
    "stacking_status": (200, {"country": "DE", "role": "master", "data": {
        "master": {"200001": {"ip": "192.0.2.28", "status": "WORKING"}},
        "slaves": {"200002": {"ip": "192.0.2.39", "status": "WORKING"},
                   "200003": {"ip": "192.0.2.66", "status": "WORKING"}},
    }}),
    "protect": (200, {"master": {"backup_buffer": 0, "protect_active": False, "serial": "200001"},
                      "slaves": [{"backup_buffer": 0, "protect_active": False, "serial": "200002"},
                                 {"backup_buffer": 0, "protect_active": False, "serial": "200003"}]}),
    "inverter_stacking": (200, {"master": {**_INVERTER, "serial": "200001"},
                                "slaves": [{**_INVERTER, "ip": "192.0.2.39", "serial": "200002"},
                                           {**_INVERTER, "ip": "192.0.2.66", "serial": "200003"}]}),
}

# a cascade's slave knows only its role: stacking_status has no data, the
# other endpoints answer "not a stack" (inverter status: 401 for User, 400 for
# Installer)
CASCADE_SLAVE = {
    "stacking_status": (200, {"country": "BE", "data": None, "role": "slave"}),
    "protect": (400, {"error": "not a stack"}),
    "inverter_stacking": (401, {"error": "401 Unauthorized"}),
}
CASCADE_SLAVE_INSTALLER = {
    "stacking_status": (200, {"country": "DE", "data": None, "role": "slave"}),
    "protect": (400, {"error": "not a stack"}),
    "inverter_stacking": (400, {"error": "not a stack"}),
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
    assert [(m.role, m.serial, m.status) for m in info.members] == [
        ("master", "100001", "WORKING"), ("slave", "100002", "WORKING")]
    assert info.members_sources == [SONNEN_API_PATH_STACKING_STATUS, SONNEN_API_PATH_STACKING_PROTECT]
    # merged by serial: fields of stacking_status and protect
    assert info.members[1].raw == {"serial": "100002", "ip": "192.0.2.114", "status": "WORKING",
                                   "backup_buffer": 0, "protect_active": False}
    assert battery.logins == 1


def test_async_cascade_master_with_inverter_status(battery):
    battery.responses = dict(CASCADE_MASTER_INSTALLER)
    info = run(async_cascade_info(battery))
    assert info.role == "master" and info.is_cascade
    assert [(m.role, m.serial, m.status) for m in info.members] == [
        ("master", "200001", "WORKING"), ("slave", "200002", "WORKING"), ("slave", "200003", "WORKING")]
    assert info.members_sources == list(CASCADE_ENDPOINTS)
    assert info.members[2].raw == {"serial": "200003", "ip": "192.0.2.66", "status": "WORKING",
                                   "backup_buffer": 0, "protect_active": False, **_INVERTER}
    assert battery.logins == 1


@pytest.mark.parametrize("responses", [CASCADE_SLAVE, CASCADE_SLAVE_INSTALLER])
def test_async_cascade_slave(battery, responses):
    battery.responses = dict(responses)
    info = run(async_cascade_info(battery))
    # a slave is a cascade, but doesn't list the members: only the master does
    assert info.role == "slave" and info.is_cascade
    assert info.members == [] and info.members_sources == []
    assert info.raw[SONNEN_API_PATH_STACKING_PROTECT] is None
    assert info.raw[SONNEN_API_PATH_INVERTER_STACKING_STATUS] is None
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
    assert info.role == "master" and [m.serial for m in info.members] == ["100001", "100002"]
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
    # stacking_status: keyed by serial number
    ({"role": "master", "data": {"master": {"1": {"status": "WORKING"}}, "slaves": {"2": {}, "3": {}}}},
     [("master", "1"), ("slave", "2"), ("slave", "3")]),
    ({"role": "master", "data": {"master": {}, "slaves": {}}}, []),
    ({"role": "none", "data": None}, []),
    (None, []),
    ([1, 2], []),
    ({"slaves": "not a list"}, []),
])
def test_parse_members(data, expected):
    assert [(m.role, m.serial) for m in parse_members(data)] == expected


def test_members_from_inverter_status_when_others_list_none():
    info = build_cascade_info({
        SONNEN_API_PATH_STACKING_STATUS: {"role": "master", "data": None},
        SONNEN_API_PATH_STACKING_PROTECT: None,
        SONNEN_API_PATH_INVERTER_STACKING_STATUS: {"master": {"serial": "1"}, "slaves": [{"serial": "2"}]},
    })
    assert info.role == "master" and info.is_cascade
    assert info.members_sources == [SONNEN_API_PATH_INVERTER_STACKING_STATUS] and len(info.members) == 2


def test_members_merged_by_serial_first_endpoint_wins():
    info = build_cascade_info({
        SONNEN_API_PATH_STACKING_STATUS: {"role": "master", "data": {
            "master": {"1": {"status": "WORKING"}}, "slaves": {"2": {"status": "ERROR"}}}},
        SONNEN_API_PATH_STACKING_PROTECT: {
            "master": {"serial": 1, "status": "other"},
            "slaves": [{"serial": "2"}, {"serial": "3"}, {"name": "no serial"}]},
        SONNEN_API_PATH_INVERTER_STACKING_STATUS: None,
    })
    assert [(m.role, m.serial, m.status) for m in info.members] == [
        ("master", "1", "WORKING"), ("slave", "2", "ERROR"), ("slave", "3", None), ("slave", None, None)]


def test_unknown_role_without_stacking_status():
    info = build_cascade_info({SONNEN_API_PATH_STACKING_STATUS: None})
    assert info.role == "unknown" and not info.is_cascade
