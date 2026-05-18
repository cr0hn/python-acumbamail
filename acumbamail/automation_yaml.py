from __future__ import annotations
from typing import Optional, TYPE_CHECKING
import yaml

if TYPE_CHECKING:
    from .automation_client import AutomationClient
    from .automation_models import Automation, AutomationNode

_TRIGGER_EVENT_MAP = {
    "subscriber_added": 0,
    "specific_date": 1,
    "segment_added": 2,
}

_WAIT_UNIT_MAP = {
    "minutes": 0,
    "hours": 1,
    "days": 2,
}


def load_yaml(path: str) -> dict:
    with open(path) as f:
        data = yaml.safe_load(f)
    validate_yaml(data)
    return data


def validate_yaml(data: dict) -> None:
    if not data.get("name"):
        raise ValueError("YAML missing required field: name")
    trigger = data.get("trigger") or {}
    if not trigger.get("list_id"):
        raise ValueError("YAML missing required field: trigger.list_id")
    event = trigger.get("event")
    if event and event not in _TRIGGER_EVENT_MAP:
        raise ValueError(f"Invalid trigger.event: {event!r}. Valid values: {list(_TRIGGER_EVENT_MAP)}")
