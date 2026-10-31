"""Exceptions raised by the sonnenbatterie clients on login problems."""
import json
import time

import aiohttp
import requests


def parse_block_time(text):
    """Return the ``block_time`` (minutes) from a failed /session reply, or None.

    The battery answers a rejected login with e.g.
    ``{"error": "401 Unauthorized", "block_time": null, "system_type": "11"}``
    and, after too many failed attempts, a number in ``block_time``.
    Never raises: a missing field, a different body (HTML, plain text, no
    JSON), null, a bool, a non-number or a non-positive number all give None.
    """
    try:
        data = json.loads(text)
    except (TypeError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    value = data.get("block_time")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if value <= 0:
        return None
    return float(value)


class LoginBlockedError(RuntimeError):
    """The battery has blocked logins for a while after too many failed
    attempts; the client refuses to log in again until the block expires so
    that it does not extend the block. No request is sent.

    ``retry_after``: seconds until the next login attempt is allowed.
    ``block_time``: the block duration (minutes) the battery reported.
    """

    def __init__(self, retry_after, block_time):
        self.retry_after = retry_after
        self.block_time = block_time
        super().__init__(
            f"Login blocked by the battery for {block_time:g} min, "
            f"next attempt allowed in {retry_after:.0f} s"
        )


class LoginError(requests.HTTPError):
    """A failed login of the synchronous client (``response`` carries the
    reply). ``block_time`` is the block duration (minutes) reported by the
    battery, or None if it did not report one."""

    def __init__(self, message, response):
        super().__init__(message, response=response)
        self.block_time = parse_block_time(response.text)


class AsyncLoginError(aiohttp.ClientResponseError):
    """A failed login of the asynchronous client (``status`` carries the HTTP
    status). ``block_time`` is the block duration (minutes) reported by the
    battery, or None if it did not report one."""

    def __init__(self, request_info, history, *, status, message, headers, block_time):
        super().__init__(request_info, history, status=status, message=message, headers=headers)
        self.block_time = block_time


class _LoginBlock:
    """Remembers a block reported by the battery (shared by both clients)."""

    def __init__(self):
        self._until = None      # time.monotonic() deadline
        self.block_time = None  # minutes, as reported

    def check(self):
        """Raise LoginBlockedError while the block is active."""
        if self._until is None:
            return
        remaining = self._until - time.monotonic()
        if remaining > 0:
            raise LoginBlockedError(remaining, self.block_time)
        self.clear()

    def set(self, block_time):
        """Start a block of ``block_time`` minutes; None means no block."""
        if block_time is None:
            return
        self.block_time = block_time
        self._until = time.monotonic() + block_time * 60

    def clear(self):
        self._until = None
        self.block_time = None
