import pytest
from acumbamail.automation_models import Automation, AutomationNode


class TestAutomationNode:
    def test_from_api_basic_fields(self):
        data = {
            "id": "234068",
            "parent_id": 0,
            "workflow": 35925,
            "nodeType": "Trigger",
            "siblings": [],
            "workflow_list": 1140700,
            "trigger_reason": {"reason_index": 0, "config": {"apply_to_subscribers_in_list": False}},
        }
        node = AutomationNode.from_api(data)
        assert node.id == "234068"
        assert node.node_type == "Trigger"
        assert node.workflow_id == 35925
        assert node.parent_id == 0
        assert node.siblings == []
        assert node.extra["workflow_list"] == 1140700

    def test_from_api_parent_id_null(self):
        data = {
            "id": "234068",
            "parent_id": None,
            "workflow": 35925,
            "nodeType": "Trigger",
            "siblings": [],
        }
        node = AutomationNode.from_api(data)
        assert node.parent_id is None

    def test_from_api_recursive_siblings(self):
        data = {
            "id": "100",
            "parent_id": 0,
            "workflow": 1,
            "nodeType": "Trigger",
            "siblings": [
                {
                    "id": "101",
                    "parent_id": 100,
                    "workflow": 1,
                    "nodeType": "Delay",
                    "wait_time": 1,
                    "wait_unit": 2,
                    "siblings": [],
                }
            ],
        }
        node = AutomationNode.from_api(data)
        assert len(node.siblings) == 1
        assert node.siblings[0].id == "101"
        assert node.siblings[0].node_type == "Delay"
        assert node.siblings[0].extra["wait_time"] == 1


class TestAutomation:
    def test_from_basic_api(self):
        data = {"id": 35925, "name": "test", "description": None, "active": True, "booting": False}
        automation = Automation.from_basic_api(data)
        assert automation.id == 35925
        assert automation.name == "test"
        assert automation.active is True
        assert automation.entry_point is None

    def test_from_full_api_with_entry_point(self):
        data = {
            "id": "35925",
            "name": "test",
            "description": None,
            "active": True,
            "booting": False,
            "entry_point": {
                "id": "234068",
                "parent_id": 0,
                "workflow": 35925,
                "nodeType": "Trigger",
                "siblings": [],
            },
        }
        automation = Automation.from_full_api(data)
        assert automation.id == 35925
        assert automation.entry_point is not None
        assert automation.entry_point.node_type == "Trigger"

    def test_from_full_api_id_as_string(self):
        data = {"id": "36215", "name": "prueba", "description": None, "active": False, "booting": False, "entry_point": None}
        automation = Automation.from_full_api(data)
        assert automation.id == 36215
        assert isinstance(automation.id, int)
