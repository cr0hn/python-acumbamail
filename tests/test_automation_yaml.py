import pytest
import yaml
from pathlib import Path
from acumbamail.automation_yaml import load_yaml, validate_yaml


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
