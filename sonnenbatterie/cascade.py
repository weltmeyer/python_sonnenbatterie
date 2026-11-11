"""Cascade information from the unofficial endpoints of the battery's web
dashboard (experimental, see README).

A cascade is a group of batteries acting as one system: one master, one or
more slaves. The dashboard reads it from three endpoints (see const.py). On
real cascade masters (sonnenBatterie 10, firmware 1.40.5; two and three units)
they answer like this:

- stacking_status: members keyed by serial number
    {"role": "master", "country": "BE",
     "data": {"master": {"100001": {"ip": "...", "status": "WORKING"}},
              "slaves": {"100002": {"ip": "...", "status": "WORKING"}}}}
- stacking/protect: members with a "serial" field
    {"master": {"serial": "100001", "backup_buffer": 0, "protect_active": false},
     "slaves": [{"serial": "100002", "backup_buffer": 0, "protect_active": false}]}
- inverter/stacking/status: HTTP 401 for User; for Installer members with a
  "serial" field, like stacking/protect
    {"master": {"serial": "200001", "grid_code_status": "set",
                "inverter_grid_code": "4901", "installed_version1": "3.18.0", ...},
     "slaves": [{"serial": "200002", "ip": "...", ...}, ...]}

Members are merged by serial number across the endpoints, so each member's
raw dict holds the fields of all of them. The raw responses are always kept in
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
    raw: dict = field(default_factory=dict)   # fields from all endpoints listing this member

    @property
    def status(self) -> Optional[str]:
        """Status from stacking_status, e.g. "WORKING"."""
        return self.raw.get("status")


@dataclass
class CascadeInfo:
    role: str                   # "none", "master", "slave" or "unknown"
    members: list = field(default_factory=list)          # [CascadeMember]
    members_sources: list = field(default_factory=list)  # endpoints the members came from
    raw: dict = field(default_factory=dict)              # endpoint -> JSON, None if not available

    @property
    def is_cascade(self) -> bool:
        return self.role not in ("none", "unknown") or len(self.members) > 1


def parse_members(data: Any) -> list:
    """Master and slaves from {"master": ..., "slaves": ...}, also when nested
    in "data" (like stacking_status). A member group is either one object with
    a "serial" field, a list of those, or objects keyed by serial number.
    Empty if the shape doesn't match."""
    if not isinstance(data, dict):
        return []
    if "master" not in data and isinstance(data.get("data"), dict):
        data = data["data"]
    return _group("master", data.get("master")) + _group("slave", data.get("slaves"))


def build_cascade_info(raw: dict) -> CascadeInfo:
    """Summarise the responses of CASCADE_ENDPOINTS (None = not available),
    merging the members of all endpoints by serial number."""
    status = raw.get(SONNEN_API_PATH_STACKING_STATUS)
    role = status.get("role") if isinstance(status, dict) else None
    info = CascadeInfo(role=role or "unknown", raw=dict(raw))
    by_serial = {}
    for path in CASCADE_ENDPOINTS:
        members = parse_members(raw.get(path))
        if not members:
            continue
        info.members_sources.append(path)
        for member in members:
            known = by_serial.get(member.serial) if member.serial is not None else None
            if known is None:
                member.raw = dict(member.raw)
                info.members.append(member)
                if member.serial is not None:
                    by_serial[member.serial] = member
            else:
                # the first endpoint wins on conflicting fields
                known.raw = {**member.raw, **known.raw}
    return info


def _group(role: str, value: Any) -> list:
    if isinstance(value, list):
        return [CascadeMember(role, _serial(m), m) for m in value if isinstance(m, dict)]
    if not isinstance(value, dict) or not value:
        return []
    if "serial" in value or not all(isinstance(v, dict) for v in value.values()):
        return [CascadeMember(role, _serial(value), value)]
    # keyed by serial number: {"100001": {"ip": ..., "status": ...}}
    return [CascadeMember(role, str(serial), {"serial": str(serial), **m}) for serial, m in value.items()]


def _serial(member: dict) -> Optional[str]:
    serial = member.get("serial")
    return None if serial is None else str(serial)
