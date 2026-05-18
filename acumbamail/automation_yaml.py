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
        trigger_payload = _update_trigger(workflow.entry_point, data.get("trigger", {}), client)
        _build_tree(workflow.id, workflow.entry_point.id, data.get("steps", []), client,
                    parent_data=trigger_payload)
        return {"workflow_id": workflow.id, "action": "created", "active": workflow.active}
    else:
        full = client.get_workflow(existing.id)
        _delete_all_nodes_except_trigger(full, client)
        trigger_payload = _update_trigger(full.entry_point, data.get("trigger", {}), client)
        _build_tree(existing.id, full.entry_point.id, data.get("steps", []), client,
                    parent_data=trigger_payload)
        return {"workflow_id": existing.id, "action": "updated", "active": existing.active}


def _update_trigger(trigger_node: "AutomationNode", trigger_data: dict,
                    client: "AutomationClient") -> dict:
    """Update trigger settings. Returns the payload dict for parent-tracking in _build_tree."""
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
    return payload


def _delete_all_nodes_except_trigger(workflow: "Automation", client: "AutomationClient") -> None:
    def _delete_subtree(node: "AutomationNode") -> None:
        for child in node.siblings:
            _delete_subtree(child)
        if node.node_type != "Trigger":
            client.delete_node(node.node_type, node.id)
    if workflow.entry_point:
        _delete_subtree(workflow.entry_point)


def _build_tree(workflow_id: int, source_id: str, steps: list, client: "AutomationClient",
               parent_data: Optional[dict] = None) -> str:
    """Build node tree. parent_data is the raw dict of the current parent node."""
    last_id = source_id
    last_data = parent_data  # track parent node data for sibling linking
    for step in steps:
        new_id, new_data = _deploy_step(workflow_id, last_id, step, client)
        # Link the new node into its parent's siblings list
        if last_data is not None:
            parent_type = (last_data.get("nodeType") or "trigger").lower()
            existing_siblings = list(last_data.get("siblings", []))
            if str(new_id) not in [str(s) for s in existing_siblings]:
                existing_siblings.append(new_id)
                updated = {**last_data, "siblings": existing_siblings}
                client.update_node(parent_type, str(last_id), updated)
                last_data["siblings"] = existing_siblings  # keep in sync
        last_id = new_id
        last_data = new_data
    return str(last_id)


def _deploy_step(workflow_id: int, source_id: str, step: dict,
                 client: "AutomationClient") -> tuple[str, dict]:
    """Deploy a single step. Returns (node_id, node_data) for parent-sibling linking."""
    stype = step["type"]

    if stype == "delay":
        node = client.create_node("Delay", workflow_id, source_id)
        updated = {**node, "wait_time": step.get("wait", 1),
                   "wait_unit": _WAIT_UNIT_MAP.get(step.get("unit", "days"), 2)}
        client.update_node("delay", node["id"], updated)
        return str(node["id"]), updated

    elif stype == "email_template":
        node = client.create_node("SendTemplate", workflow_id, source_id,
                                  extra={"template": step["template_id"]})
        update = {k: v for k, v in node.items() if k not in ("from_email", "from_name")}
        update.update({
            "name": step.get("name", f"step-{node['id']}"),
            "subject": step["subject"],
            "preheader": step.get("preheader", ""),
            "template": step["template_id"],
            "tracking_urls": step.get("track_urls", True),
            "tracking_analytics": step.get("track_analytics", True),
        })
        if "from_email" in step:
            update["from_email"] = step["from_email"]
        if "from_name" in step:
            update["from_name"] = step["from_name"]
        client.update_node("sendtemplate", node["id"], update)
        return str(node["id"]), update

    elif stype == "plain_email":
        node = client.create_node("SendPlainEmail", workflow_id, source_id)
        updated = {**node, "subject": step["subject"], "content": step["content"]}
        if "from_email" in step:
            updated["from_email"] = step["from_email"]
        if "from_name" in step:
            updated["from_name"] = step["from_name"]
        client.update_node("sendplainemail", node["id"], updated)
        return str(node["id"]), updated

    elif stype == "webhook":
        node = client.create_node("Webhook", workflow_id, source_id)
        updated = {**node, "url": step["url"], "method": step.get("method", "POST")}
        client.update_node("webhook", node["id"], updated)
        return str(node["id"]), updated

    elif stype == "update_field":
        node = client.create_node("UpdateField", workflow_id, source_id)
        updated = {**node, "field_name": step["field"], "field_value": step["value"]}
        client.update_node("updatefield", node["id"], updated)
        return str(node["id"]), updated

    elif stype == "move_to":
        node = client.create_node("MoveTo", workflow_id, source_id)
        updated = {**node, "target_list_id": step["list_id"]}
        client.update_node("moveto", node["id"], updated)
        return str(node["id"]), updated

    elif stype == "condition":
        # Fork is the parent of both branches; no merge point exists in the Acumbamail model.
        fork = client.create_node("Fork", workflow_id, source_id)
        cond_true = client.create_node("Condition", workflow_id, fork["id"])
        ct_data = {**cond_true, "evaluation": True}
        client.update_node("condition", cond_true["id"], ct_data)
        _build_tree(workflow_id, cond_true["id"], step.get("on_match", []), client,
                    parent_data=ct_data)
        cond_false = client.create_node("Condition", workflow_id, fork["id"])
        cf_data = {**cond_false, "evaluation": False}
        client.update_node("condition", cond_false["id"], cf_data)
        _build_tree(workflow_id, cond_false["id"], step.get("on_no_match", []), client,
                    parent_data=cf_data)
        return str(fork["id"]), fork

    elif stype == "until":
        node = client.create_node("Until", workflow_id, source_id)
        _build_tree(workflow_id, node["id"], step.get("steps", []), client,
                    parent_data=node)
        return str(node["id"]), node

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


_BRANCHING_TYPES = {"Fork", "Condition", "Until"}


def _nodes_to_steps(nodes: list) -> list:
    """Convert a list of nodes to YAML steps, following linear chains through siblings."""
    steps = []
    for node in nodes:
        step = _node_to_step(node)
        if step is not None:
            steps.append(step)
        # For linear nodes, follow their siblings as the next steps in the chain.
        # Branching nodes (Fork/Condition/Until) already handle their own siblings internally.
        if node.node_type not in _BRANCHING_TYPES and node.siblings:
            steps.extend(_nodes_to_steps(node.siblings))
    return steps


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
