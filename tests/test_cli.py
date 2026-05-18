"""Tests del CLI de Acumbamail."""
import json
import os
import pytest
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner

runner = CliRunner()


class TestGetClient:
    def test_uses_token_flag_over_env(self):
        from acumbamail.cli.utils import get_client
        with patch.dict(os.environ, {"ACUMBAMAIL_TOKEN": "env_token"}):
            client = get_client(token="flag_token")
        assert client.auth_token == "flag_token"

    def test_uses_env_when_no_flag(self):
        from acumbamail.cli.utils import get_client
        with patch.dict(os.environ, {"ACUMBAMAIL_TOKEN": "env_token"}):
            client = get_client(token=None)
        assert client.auth_token == "env_token"

    def test_raises_when_no_token(self):
        from acumbamail.cli.utils import get_client
        env = {k: v for k, v in os.environ.items() if k != "ACUMBAMAIL_TOKEN"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(SystemExit):
                get_client(token=None)


class TestPrintJson:
    def test_outputs_dict_as_json(self, capsys):
        from acumbamail.cli.utils import print_json
        print_json({"key": "value", "num": 42})
        captured = capsys.readouterr()
        assert json.loads(captured.out) == {"key": "value", "num": 42}

    def test_outputs_list_as_json(self, capsys):
        from acumbamail.cli.utils import print_json
        print_json([{"id": 1}, {"id": 2}])
        captured = capsys.readouterr()
        assert json.loads(captured.out) == [{"id": 1}, {"id": 2}]


class TestListsCommands:
    def test_lists_list_outputs_json(self):
        from acumbamail.cli.main import app
        from acumbamail.models import MailList

        mock_lists = [MailList(id=123, name="Newsletter", description="", subscribers_count=100)]
        with patch("acumbamail.cli.commands.lists.get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.get_lists.return_value = mock_lists
            mock_get_client.return_value = mock_client

            result = runner.invoke(app, ["--token", "tk", "lists", "list"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data[0]["id"] == 123
        assert data[0]["name"] == "Newsletter"

    def test_lists_create_outputs_created_list(self):
        from acumbamail.cli.main import app
        from acumbamail.models import MailList

        mock_list = MailList(id=456, name="New List", description="")
        with patch("acumbamail.cli.commands.lists.get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.create_list.return_value = mock_list
            mock_get_client.return_value = mock_client

            result = runner.invoke(app, [
                "--token", "tk", "lists", "create",
                "--name", "New List", "--sender-email", "s@x.com"
            ])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == 456

    def test_lists_delete_exits_zero(self):
        from acumbamail.cli.main import app
        with patch("acumbamail.cli.commands.lists.get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.delete_list.return_value = None
            mock_get_client.return_value = mock_client

            result = runner.invoke(app, ["--token", "tk", "lists", "delete", "--list-id", "123"])

        assert result.exit_code == 0

    def test_lists_stats_outputs_dict(self):
        from acumbamail.cli.main import app
        with patch("acumbamail.cli.commands.lists.get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.get_list_stats.return_value = {"total_subscribers": 50}
            mock_get_client.return_value = mock_client

            result = runner.invoke(app, ["--token", "tk", "lists", "stats", "--list-id", "123"])

        assert result.exit_code == 0
        assert json.loads(result.output)["total_subscribers"] == 50
