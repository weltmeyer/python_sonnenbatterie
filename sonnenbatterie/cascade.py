"""Cascade information from the unofficial endpoints of the battery's web
dashboard (experimental, see README).

A cascade is a group of batteries acting as one system: one master, one or
more slaves. The dashboard reads it from three endpoints (see const.py); their
response on a real cascade is unconfirmed so far, so the parsing here is based
on how the dashboard's code uses them: {"master": {"serial": ...},
"slaves": [{"serial": ...}, ...]}. The raw responses are always kept in
CascadeInfo.raw, so callers can work with fields not parsed yet.
"""
from dataclasses import dataclass, field
from typing import Any, Optional

from .const import (
    SONNEN_API_PATH_INVERTER_STACKING_STATUS,
    SONNEN_API_PATH_STACKING_PROTECT,
    SONNEN_API_PATH_STACKING_STATUS,
)

# all endpoints get_cascade_info() reads, in this order
CASCADE_ENDPOINTS = (
    SONNEN_API_PATH_STACKING_STATUS,
    SONNEN_API_PATH_STACKING_PROTECT,
    SONNEN_API_PATH_INVERTER_STACKING_STATUS,
)

# HTTP status codes meaning "not available here" rather than an error:
# 400 "not a stack" (single battery), 401/403 role not permitted, 404 firmware
# without the endpoint
NOT_AVAILABLE = (400, 401, 403, 404)


@dataclass
class CascadeMember:
    role: str                   # "master" or "slave"
    serial: Optional[str]
    raw: dict = field(default_factory=dict)


@dataclass
class CascadeInfo:
    role: str                   # "none", "master", "slave" or "unknown"
    members: list = field(default_factory=list)          # [CascadeMember]
    members_source: Optional[str] = None                 # endpoint the members came from
    raw: dict = field(default_factory=dict)              # endpoint -> JSON, None if not available

    @property
    def is_cascade(self) -> bool:
        return self.role not in ("none", "unknown") or len(self.members) > 1


def parse_members(data: Any) -> list:
    """Master and slaves from {"master": {...}, "slaves": [...]}, also when
    nested in "data" (like stacking_status). Empty if the shape doesn't match."""
    if not isinstance(data, dict):
        return []
    if "master" not in data and isinstance(data.get("data"), dict):
        data = data["data"]
    members = []
    master = data.get("master")
    if isinstance(master, dict):
        members.append(CascadeMember("master", _serial(master), master))
    slaves = data.get("slaves")
    if isinstance(slaves, list):
        members += [CascadeMember("slave", _serial(s), s) for s in slaves if isinstance(s, dict)]
    return members


def build_cascade_info(raw: dict) -> CascadeInfo:
    """Summarise the responses of CASCADE_ENDPOINTS (None = not available)."""
    status = raw.get(SONNEN_API_PATH_STACKING_STATUS)
    role = status.get("role") if isinstance(status, dict) else None
    info = CascadeInfo(role=role or "unknown", raw=dict(raw))
    for path in CASCADE_ENDPOINTS:
        members = parse_members(raw.get(path))
        if members:
            info.members, info.members_source = members, path
            break
    return info


def _serial(member: dict) -> Optional[str]:
    serial = member.get("serial")
    return None if serial is None else str(serial)
