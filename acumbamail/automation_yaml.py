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

_INV_TRIGGER_EVENT_MAP: dict[int, str] = {v: k for k, v in _TRIGGER_EVENT_MAP.items()}
_INV_WAIT_UNIT_MAP: dict[int, str] = {v: k for k, v in _WAIT_UNIT_MAP.items()}


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


def deploy_yaml(data: dict, client: "AutomationClient") -> dict:
    name = data["name"]
    description = data.get("description")
    existing = next((w for w in client.list_workflows() if w.name == name), None)

    if existing is None:
        workflow = client.create_workflow(name, description)
        trigger_id = workflow.entry_point.id
        _update_trigger(workflow.entry_point, data.get("trigger", {}), client)
        _build_tree(workflow.id, trigger_id, data.get("steps", []), client)
        return {"workflow_id": workflow.id, "action": "created", "active": workflow.active}
    else:
        full = client.get_workflow(existing.id)
        _delete_all_nodes_except_trigger(full, client)
        _update_trigger(full.entry_point, data.get("trigger", {}), client)
        _build_tree(existing.id, full.entry_point.id, data.get("steps", []), client)
        return {"workflow_id": existing.id, "action": "updated", "active": existing.active}


def _update_trigger(trigger_node: "AutomationNode", trigger_data: dict, client: "AutomationClient") -> None:
    reason_index = _TRIGGER_EVENT_MAP.get(trigger_data.get("event", "subscriber_added"), 0)
    payload = {
        **trigger_node.extra,
        "id": trigger_node.id,
        "nodeType": "Trigger",
        "workflow": trigger_node.workflow_id,
        "siblings": [s.id for s in trigger_node.siblings],
        "workflow_list": trigger_data.get("list_id", trigger_node.extra.get("workflow_list")),
        "trigger_reason": {
            "reason_index": reason_index,
            "config": {"apply_to_subscribers_in_list": trigger_data.get("apply_to_existing", False)},
        },
    }
    client.update_node("trigger", trigger_node.id, payload)


def _delete_all_nodes_except_trigger(workflow: "Automation", client: "AutomationClient") -> None:
    def _delete_subtree(node: "AutomationNode") -> None:
        for child in node.siblings:
            _delete_subtree(child)
        if node.node_type != "Trigger":
            client.delete_node(node.node_type, node.id)
    if workflow.entry_point:
        _delete_subtree(workflow.entry_point)


def _build_tree(workflow_id: int, source_id: str, steps: list, client: "AutomationClient") -> str:
    last_id = source_id
    for step in steps:
        last_id = _deploy_step(workflow_id, last_id, step, client)
    return last_id


def _deploy_step(workflow_id: int, source_id: str, step: dict, client: "AutomationClient") -> str:
    stype = step["type"]

    if stype == "delay":
        node = client.create_node("Delay", workflow_id, source_id)
        client.update_node("delay", node["id"], {
            **node,
            "wait_time": step.get("wait", 1),
            "wait_unit": _WAIT_UNIT_MAP.get(step.get("unit", "days"), 2),
        })
        return str(node["id"])

    elif stype == "email_template":
        node = client.create_node("SendTemplate", workflow_id, source_id)
        client.update_node("sendtemplate", node["id"], {
            **node,
            "name": step.get("name", f"step-{node['id']}"),
            "subject": step["subject"],
            "preheader": step.get("preheader", ""),
            "from_email": step["from_email"],
            "from_name": step["from_name"],
            "template": step["template_id"],
            "tracking_urls": step.get("track_urls", True),
            "tracking_analytics": step.get("track_analytics", True),
        })
        return str(node["id"])

    elif stype == "plain_email":
        node = client.create_node("SendPlainEmail", workflow_id, source_id)
        client.update_node("sendplainemail", node["id"], {
            **node,
            "subject": step["subject"],
            "from_email": step["from_email"],
            "from_name": step["from_name"],
            "content": step["content"],
        })
        return str(node["id"])

    elif stype == "webhook":
        node = client.create_node("Webhook", workflow_id, source_id)
        client.update_node("webhook", node["id"], {
            **node,
            "url": step["url"],
            "method": step.get("method", "POST"),
        })
        return str(node["id"])

    elif stype == "update_field":
        node = client.create_node("UpdateField", workflow_id, source_id)
        client.update_node("updatefield", node["id"], {**node, "field_name": step["field"], "field_value": step["value"]})
        return str(node["id"])

    elif stype == "move_to":
        node = client.create_node("MoveTo", workflow_id, source_id)
        client.update_node("moveto", node["id"], {**node, "target_list_id": step["list_id"]})
        return str(node["id"])

    elif stype == "condition":
        # Fork is the parent of both branches; no merge point exists in the Acumbamail model.
        # Steps after a condition in the parent list attach to the Fork node.
        fork = client.create_node("Fork", workflow_id, source_id)
        cond_true = client.create_node("Condition", workflow_id, fork["id"])
        client.update_node("condition", cond_true["id"], {**cond_true, "evaluation": True})
        _build_tree(workflow_id, cond_true["id"], step.get("on_match", []), client)
        cond_false = client.create_node("Condition", workflow_id, fork["id"])
        client.update_node("condition", cond_false["id"], {**cond_false, "evaluation": False})
        _build_tree(workflow_id, cond_false["id"], step.get("on_no_match", []), client)
        return str(fork["id"])

    elif stype == "until":
        node = client.create_node("Until", workflow_id, source_id)
        _build_tree(workflow_id, node["id"], step.get("steps", []), client)
        return str(node["id"])

    else:
        raise ValueError(f"Unknown step type: {stype!r}")


def export_yaml(workflow: "Automation") -> dict:
    if workflow.entry_point is None:
        raise ValueError(f"Workflow '{workflow.name}' has no entry_point — cannot export")
    result: dict = {"name": workflow.name}
    if workflow.description:
        result["description"] = workflow.description

    trigger = workflow.entry_point
    ev_inv = _INV_TRIGGER_EVENT_MAP
    reason = trigger.extra.get("trigger_reason") or {}
    result["trigger"] = {
        "list_id": trigger.extra.get("workflow_list"),
        "event": ev_inv.get(reason.get("reason_index", 0), "subscriber_added"),
        "apply_to_existing": (reason.get("config") or {}).get("apply_to_subscribers_in_list", False),
    }
    result["steps"] = _nodes_to_steps(trigger.siblings)

    return result


def _nodes_to_steps(nodes: list) -> list:
    return [s for s in (_node_to_step(n) for n in nodes) if s is not None]


def _node_to_step(node: "AutomationNode") -> Optional[dict]:
    unit_inv = _INV_WAIT_UNIT_MAP
    nt = node.node_type

    if nt == "Delay":
        return {"type": "delay", "wait": node.extra.get("wait_time", 1),
                "unit": unit_inv.get(node.extra.get("wait_unit", 2), "days")}
    elif nt == "SendTemplate":
        step: dict = {"type": "email_template", "subject": node.extra.get("subject", ""),
                      "from_email": node.extra.get("from_email", ""), "from_name": node.extra.get("from_name", ""),
                      "template_id": node.extra.get("template")}
        if node.extra.get("preheader"):
            step["preheader"] = node.extra["preheader"]
        return step
    elif nt == "SendPlainEmail":
        return {"type": "plain_email", "subject": node.extra.get("subject", ""),
                "from_email": node.extra.get("from_email", ""), "from_name": node.extra.get("from_name", ""),
                "content": node.extra.get("content", "")}
    elif nt == "Webhook":
        return {"type": "webhook", "url": node.extra.get("url", ""), "method": node.extra.get("method", "POST")}
    elif nt == "UpdateField":
        return {"type": "update_field", "field": node.extra.get("field_name", ""),
                "value": node.extra.get("field_value", "")}
    elif nt == "MoveTo":
        return {"type": "move_to", "list_id": node.extra.get("target_list_id")}
    elif nt == "Fork":
        on_match, on_no_match = [], []
        for child in node.siblings:
            if child.node_type == "Condition":
                if child.extra.get("evaluation"):
                    on_match = _nodes_to_steps(child.siblings)
                else:
                    on_no_match = _nodes_to_steps(child.siblings)
        return {"type": "condition", "on_match": on_match, "on_no_match": on_no_match}
    elif nt == "Until":
        return {"type": "until", "steps": _nodes_to_steps(node.siblings)}
    return None
