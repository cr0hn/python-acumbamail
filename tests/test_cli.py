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
