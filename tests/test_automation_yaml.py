import pytest
import yaml
from pathlib import Path
from unittest.mock import MagicMock
from acumbamail.automation_yaml import load_yaml, validate_yaml, deploy_yaml, _build_tree, _deploy_step
from acumbamail.automation_models import Automation, AutomationNode


class TestLoadYaml:
    def test_load_valid_yaml(self, tmp_path):
        p = tmp_path / "wf.yaml"
        p.write_text("""
name: test-automation
trigger:
  list_id: 1138335
  event: subscriber_added
steps:
  - type: delay
    wait: 1
    unit: days
""")
        data = load_yaml(str(p))
        assert data["name"] == "test-automation"
        assert data["trigger"]["list_id"] == 1138335
        assert data["steps"][0]["type"] == "delay"

    def test_load_raises_on_missing_file(self):
        with pytest.raises(FileNotFoundError):
            load_yaml("/nonexistent/path/file.yaml")


class TestValidateYaml:
    def test_raises_if_name_missing(self):
        with pytest.raises(ValueError, match="name"):
            validate_yaml({"trigger": {"list_id": 1}})

    def test_raises_if_list_id_missing(self):
        with pytest.raises(ValueError, match="list_id"):
            validate_yaml({"name": "test", "trigger": {}})

    def test_raises_on_invalid_event(self):
        with pytest.raises(ValueError, match="event"):
            validate_yaml({"name": "test", "trigger": {"list_id": 1, "event": "invalid_event"}})

    def test_valid_minimal_yaml_passes(self):
        validate_yaml({"name": "test", "trigger": {"list_id": 1138335}})

    def test_valid_yaml_with_event_passes(self):
        validate_yaml({"name": "test", "trigger": {"list_id": 1138335, "event": "subscriber_added"}})
        validate_yaml({"name": "test", "trigger": {"list_id": 1138335, "event": "specific_date"}})
        validate_yaml({"name": "test", "trigger": {"list_id": 1138335, "event": "segment_added"}})


def make_trigger_node(node_id="234068"):
    return AutomationNode(
        id=node_id, node_type="Trigger", workflow_id=35925,
        parent_id=0, siblings=[], extra={"workflow_list": 1138335},
    )

def make_automation(wf_id=35925, name="test", trigger_id="234068"):
    return Automation(
        id=wf_id, name=name, description=None, active=False, booting=False,
        entry_point=make_trigger_node(trigger_id),
    )


class TestDeployStep:
    def test_delay_creates_and_updates_node(self):
        client = MagicMock()
        client.create_node.return_value = {
            "id": "111", "nodeType": "Delay", "workflow": 1, "siblings": [],
            "wait_time": 1, "wait_unit": 2,
        }
        step = {"type": "delay", "wait": 3, "unit": "days"}
        node_id = _deploy_step(35925, "234068", step, client)
        client.create_node.assert_called_once_with("Delay", 35925, "234068")
        client.update_node.assert_called_once()
        update_args = client.update_node.call_args[0]
        assert update_args[0] == "delay"
        assert update_args[1] == "111"
        assert update_args[2]["wait_time"] == 3
        assert update_args[2]["wait_unit"] == 2
        assert node_id == "111"

    def test_delay_unit_minutes(self):
        client = MagicMock()
        client.create_node.return_value = {"id": "111", "nodeType": "Delay", "workflow": 1, "siblings": []}
        _deploy_step(1, "100", {"type": "delay", "wait": 5, "unit": "minutes"}, client)
        update_args = client.update_node.call_args[0][2]
        assert update_args["wait_unit"] == 0

    def test_email_template_creates_and_updates(self):
        client = MagicMock()
        client.create_node.return_value = {
            "id": "222", "nodeType": "SendTemplate", "workflow": 1, "siblings": [],
        }
        step = {
            "type": "email_template",
            "subject": "Hello!",
            "from_email": "a@b.com",
            "from_name": "A",
            "template_id": 9999,
        }
        node_id = _deploy_step(1, "100", step, client)
        update_args = client.update_node.call_args[0][2]
        assert update_args["subject"] == "Hello!"
        assert update_args["template"] == 9999
        assert update_args["from_email"] == "a@b.com"
        assert node_id == "222"

    def test_webhook_creates_and_updates(self):
        client = MagicMock()
        client.create_node.return_value = {"id": "333", "nodeType": "Webhook", "workflow": 1, "siblings": []}
        node_id = _deploy_step(1, "100", {"type": "webhook", "url": "https://x.com/hook", "method": "POST"}, client)
        update_args = client.update_node.call_args[0][2]
        assert update_args["url"] == "https://x.com/hook"
        assert node_id == "333"

    def test_unknown_type_raises(self):
        client = MagicMock()
        with pytest.raises(ValueError, match="Unknown step type"):
            _deploy_step(1, "100", {"type": "unknown_type"}, client)


class TestDeployYaml:
    def test_creates_new_workflow_when_not_found(self):
        client = MagicMock()
        client.list_workflows.return_value = []
        client.create_workflow.return_value = make_automation()
        client.create_node.return_value = {
            "id": "500", "nodeType": "Delay", "workflow": 35925, "siblings": [],
        }
        data = {
            "name": "test",
            "trigger": {"list_id": 1138335, "event": "subscriber_added"},
            "steps": [{"type": "delay", "wait": 1, "unit": "days"}],
        }
        result = deploy_yaml(data, client)
        client.create_workflow.assert_called_once_with("test", None)
        assert result["action"] == "created"
        assert result["workflow_id"] == 35925

    def test_returns_updated_when_workflow_exists(self):
        client = MagicMock()
        existing = make_automation()
        client.list_workflows.return_value = [existing]
        client.get_workflow.return_value = make_automation()
        data = {
            "name": "test",
            "trigger": {"list_id": 1138335},
            "steps": [],
        }
        result = deploy_yaml(data, client)
        client.create_workflow.assert_not_called()
        assert result["action"] == "updated"


from acumbamail.automation_yaml import export_yaml


def make_node(node_id, node_type, workflow_id=1, siblings=None, **extra):
    return AutomationNode(
        id=str(node_id), node_type=node_type, workflow_id=workflow_id,
        parent_id=0, siblings=siblings or [], extra=extra,
    )


class TestExportYaml:
    def test_exports_name_and_description(self):
        wf = Automation(id=1, name="test", description="my desc", active=False, booting=False,
                        entry_point=make_node(100, "Trigger", workflow_list=1138335,
                                              trigger_reason={"reason_index": 0, "config": {"apply_to_subscribers_in_list": False}}))
        result = export_yaml(wf)
        assert result["name"] == "test"
        assert result["description"] == "my desc"

    def test_exports_trigger_list_id_and_event(self):
        trigger = make_node(100, "Trigger", workflow_list=1138335,
                            trigger_reason={"reason_index": 0, "config": {"apply_to_subscribers_in_list": False}})
        wf = Automation(id=1, name="test", description=None, active=False, booting=False, entry_point=trigger)
        result = export_yaml(wf)
        assert result["trigger"]["list_id"] == 1138335
        assert result["trigger"]["event"] == "subscriber_added"
        assert result["trigger"]["apply_to_existing"] is False

    def test_exports_delay_step(self):
        delay = make_node(200, "Delay", wait_time=3, wait_unit=2)
        trigger = make_node(100, "Trigger", workflow_list=1138335,
                            trigger_reason={"reason_index": 0, "config": {}}, siblings=[delay])
        wf = Automation(id=1, name="test", description=None, active=False, booting=False, entry_point=trigger)
        result = export_yaml(wf)
        assert result["steps"][0]["type"] == "delay"
        assert result["steps"][0]["wait"] == 3
        assert result["steps"][0]["unit"] == "days"

    def test_exports_email_template_step(self):
        email = make_node(200, "SendTemplate", subject="Hi!", from_email="a@b.com",
                          from_name="A", template=9999, preheader="preview")
        trigger = make_node(100, "Trigger", workflow_list=1138335,
                            trigger_reason={"reason_index": 0, "config": {}}, siblings=[email])
        wf = Automation(id=1, name="test", description=None, active=False, booting=False, entry_point=trigger)
        result = export_yaml(wf)
        step = result["steps"][0]
        assert step["type"] == "email_template"
        assert step["subject"] == "Hi!"
        assert step["template_id"] == 9999
        assert step["preheader"] == "preview"

    def test_exports_condition_as_on_match_on_no_match(self):
        cond_true = make_node(301, "Condition", evaluation=True)
        cond_false = make_node(302, "Condition", evaluation=False)
        fork = make_node(300, "Fork", siblings=[cond_true, cond_false])
        trigger = make_node(100, "Trigger", workflow_list=1138335,
                            trigger_reason={"reason_index": 0, "config": {}}, siblings=[fork])
        wf = Automation(id=1, name="test", description=None, active=False, booting=False, entry_point=trigger)
        result = export_yaml(wf)
        step = result["steps"][0]
        assert step["type"] == "condition"
        assert "on_match" in step
        assert "on_no_match" in step
