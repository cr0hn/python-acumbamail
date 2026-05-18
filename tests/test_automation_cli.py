import json
import pytest
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
from acumbamail.automation_models import Automation

runner = CliRunner()
ENV = {"ACUMBAMAIL_EMAIL": "user@test.com", "ACUMBAMAIL_PASSWORD": "secret"}

BASIC_WF = Automation(id=35925, name="email-bienvenida", description=None, active=True, booting=False)


def make_mock_client(workflows=None):
    client = MagicMock()
    client.list_workflows.return_value = workflows or [BASIC_WF]
    return client


class TestAutomationsList:
    def test_outputs_json_list(self):
        from acumbamail.cli.main import app
        with patch("acumbamail.cli.commands.automations.get_automation_client") as mock_fn:
            mock_fn.return_value = make_mock_client()
            result = runner.invoke(app, ["automations", "list"], env=ENV)
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data[0]["id"] == 35925
        assert data[0]["name"] == "email-bienvenida"

    def test_exits_1_without_credentials(self):
        from acumbamail.cli.main import app
        # Patch session file to not exist so we fall through to credential check
        with patch("acumbamail.cli.utils.os.path.exists", return_value=False):
            result = runner.invoke(app, ["automations", "list"], env={})
        assert result.exit_code == 1


class TestAutomationsDeploy:
    def test_deploy_creates_workflow(self, tmp_path):
        from acumbamail.cli.main import app
        p = tmp_path / "wf.yaml"
        p.write_text("name: test\ntrigger:\n  list_id: 1138335\nsteps: []\n")
        with patch("acumbamail.cli.commands.automations.get_automation_client") as mock_fn:
            with patch("acumbamail.cli.commands.automations.deploy_yaml") as mock_deploy:
                mock_fn.return_value = MagicMock()
                mock_deploy.return_value = {"workflow_id": 999, "action": "created", "active": False}
                result = runner.invoke(app, ["automations", "deploy", str(p)], env=ENV)
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["action"] == "created"

    def test_deploy_exits_1_on_missing_file(self):
        from acumbamail.cli.main import app
        with patch("acumbamail.cli.commands.automations.get_automation_client"):
            result = runner.invoke(app, ["automations", "deploy", "/no/such/file.yaml"], env=ENV)
        assert result.exit_code == 1


class TestAutomationsDelete:
    def test_delete_by_id(self):
        from acumbamail.cli.main import app
        with patch("acumbamail.cli.commands.automations.get_automation_client") as mock_fn:
            mock_client = make_mock_client()
            mock_fn.return_value = mock_client
            result = runner.invoke(app, ["automations", "delete", "--id", "35925"], env=ENV)
        assert result.exit_code == 0, result.output
        mock_client.delete_workflow.assert_called_once_with(35925)

    def test_delete_by_name(self):
        from acumbamail.cli.main import app
        with patch("acumbamail.cli.commands.automations.get_automation_client") as mock_fn:
            mock_client = make_mock_client()
            mock_fn.return_value = mock_client
            result = runner.invoke(app, ["automations", "delete", "--name", "email-bienvenida"], env=ENV)
        assert result.exit_code == 0, result.output
        mock_client.delete_workflow.assert_called_once_with(35925)

    def test_delete_exits_1_if_name_not_found(self):
        from acumbamail.cli.main import app
        with patch("acumbamail.cli.commands.automations.get_automation_client") as mock_fn:
            mock_fn.return_value = make_mock_client()
            result = runner.invoke(app, ["automations", "delete", "--name", "nonexistent"], env=ENV)
        assert result.exit_code == 1


class TestAutomationsExport:
    def test_export_by_id_outputs_yaml(self):
        from acumbamail.cli.main import app
        from acumbamail.automation_models import AutomationNode
        trigger = AutomationNode(id="100", node_type="Trigger", workflow_id=35925,
                                 parent_id=0, siblings=[], extra={"workflow_list": 1138335,
                                 "trigger_reason": {"reason_index": 0, "config": {}}})
        full_wf = Automation(id=35925, name="email-bienvenida", description=None,
                             active=True, booting=False, entry_point=trigger)
        with patch("acumbamail.cli.commands.automations.get_automation_client") as mock_fn:
            mock_client = make_mock_client()
            mock_client.get_workflow.return_value = full_wf
            mock_fn.return_value = mock_client
            result = runner.invoke(app, ["automations", "export", "--id", "35925"], env=ENV)
        assert result.exit_code == 0, result.output
        assert "email-bienvenida" in result.output
        assert "subscriber_added" in result.output
