from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class AutomationNode:
    id: str
    node_type: str
    workflow_id: int
    parent_id: Optional[int]
    siblings: list[AutomationNode]
    extra: Dict[str, Any]

    @classmethod
    def from_api(cls, data: dict) -> AutomationNode:
        siblings = [cls.from_api(s) for s in data.get("siblings", [])]
        skip = {"id", "nodeType", "workflow", "parent_id", "siblings"}
        extra = {k: v for k, v in data.items() if k not in skip}
        return cls(
            id=str(data["id"]),
            node_type=data["nodeType"],
            workflow_id=int(data["workflow"]),
            parent_id=int(data["parent_id"]) if data.get("parent_id") is not None else None,
            siblings=siblings,
            extra=extra,
        )


@dataclass
class Automation:
    id: int
    name: str
    description: Optional[str]
    active: bool
    booting: bool
    entry_point: Optional[AutomationNode] = None

    @classmethod
    def from_basic_api(cls, data: dict) -> Automation:
        return cls(
            id=int(data["id"]),
            name=data["name"],
            description=data.get("description"),
            active=data["active"],
            booting=data["booting"],
        )

    @classmethod
    def from_full_api(cls, data: dict) -> Automation:
        entry_point = None
        if data.get("entry_point"):
            entry_point = AutomationNode.from_api(data["entry_point"])
        return cls(
            id=int(data["id"]),
            name=data["name"],
            description=data.get("description"),
            active=data["active"],
            booting=data["booting"],
            entry_point=entry_point,
        )
