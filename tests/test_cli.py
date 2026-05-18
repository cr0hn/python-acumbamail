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


class TestSubscribersCommands:
    def test_subscribers_list_outputs_json(self):
        from acumbamail.cli.main import app
        from acumbamail.models import Subscriber

        mock_subs = [Subscriber(email="a@test.com", list_id=123, is_active=True)]
        with patch("acumbamail.cli.commands.subscribers.get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.get_subscribers.return_value = mock_subs
            mock_get_client.return_value = mock_client

            result = runner.invoke(app, ["--token", "tk", "subscribers", "list", "--list-id", "123"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data[0]["email"] == "a@test.com"

    def test_subscribers_add_outputs_subscriber(self):
        from acumbamail.cli.main import app
        from acumbamail.models import Subscriber

        with patch("acumbamail.cli.commands.subscribers.get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.add_subscriber.return_value = Subscriber(email="b@test.com", list_id=123)
            mock_get_client.return_value = mock_client

            result = runner.invoke(app, [
                "--token", "tk", "subscribers", "add",
                "--list-id", "123", "--email", "b@test.com"
            ])

        assert result.exit_code == 0
        assert json.loads(result.output)["email"] == "b@test.com"

    def test_subscribers_delete_exits_zero(self):
        from acumbamail.cli.main import app
        with patch("acumbamail.cli.commands.subscribers.get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.delete_subscriber.return_value = None
            mock_get_client.return_value = mock_client

            result = runner.invoke(app, [
                "--token", "tk", "subscribers", "delete",
                "--list-id", "123", "--email", "b@test.com"
            ])

        assert result.exit_code == 0

    def test_subscribers_search_outputs_list(self):
        from acumbamail.cli.main import app
        from acumbamail.models import SubscriberDetails

        mock_results = [SubscriberDetails(id=1, email="c@test.com", status="active")]
        with patch("acumbamail.cli.commands.subscribers.get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.search_subscriber.return_value = mock_results
            mock_get_client.return_value = mock_client

            result = runner.invoke(app, ["--token", "tk", "subscribers", "search", "--query", "c@test.com"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data[0]["email"] == "c@test.com"

    def test_subscribers_unsubscribe_exits_zero(self):
        from acumbamail.cli.main import app
        with patch("acumbamail.cli.commands.subscribers.get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.unsubscribe_subscriber.return_value = None
            mock_get_client.return_value = mock_client

            result = runner.invoke(app, [
                "--token", "tk", "subscribers", "unsubscribe",
                "--list-id", "123", "--email", "c@test.com"
            ])

        assert result.exit_code == 0

    def test_subscribers_batch_add_from_file(self, tmp_path):
        from acumbamail.cli.main import app
        from acumbamail.models import BatchSubscriberResult

        subs_file = tmp_path / "subs.json"
        subs_file.write_text('[{"email": "x@test.com"}, {"email": "y@test.com"}]')

        mock_results = [
            BatchSubscriberResult(email="x@test.com", subscriber_id=1),
            BatchSubscriberResult(email="y@test.com", subscriber_id=2),
        ]
        with patch("acumbamail.cli.commands.subscribers.get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.batch_add_subscribers.return_value = mock_results
            mock_get_client.return_value = mock_client

            result = runner.invoke(app, [
                "--token", "tk", "subscribers", "batch-add",
                "--list-id", "123", "--file", str(subs_file)
            ])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 2
        assert data[0]["email"] == "x@test.com"


class TestCampaignsCommands:
    def test_campaigns_list_outputs_json(self):
        from acumbamail.cli.main import app
        from acumbamail.models import Campaign

        mock_campaigns = [
            Campaign(id=1, name="Camp1", subject="Subj", content="", from_name="X", from_email="x@x.com", list_ids=[1])
        ]
        with patch("acumbamail.cli.commands.campaigns.get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.get_campaigns.return_value = mock_campaigns
            mock_get_client.return_value = mock_client

            result = runner.invoke(app, ["--token", "tk", "campaigns", "list"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data[0]["id"] == 1
        assert data[0]["name"] == "Camp1"

    def test_campaigns_info_outputs_dict(self):
        from acumbamail.cli.main import app
        with patch("acumbamail.cli.commands.campaigns.get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.get_campaign_basic_information.return_value = {"id": 1, "name": "Camp1"}
            mock_get_client.return_value = mock_client

            result = runner.invoke(app, ["--token", "tk", "campaigns", "info", "--campaign-id", "1"])

        assert result.exit_code == 0
        assert json.loads(result.output)["id"] == 1

    def test_campaigns_stats_outputs_dict(self):
        from acumbamail.cli.main import app
        from acumbamail.models import CampaignTotalInformation

        mock_stats = CampaignTotalInformation(total_delivered=100, opened=50, unique_clicks=20)
        with patch("acumbamail.cli.commands.campaigns.get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.get_campaign_total_information.return_value = mock_stats
            mock_get_client.return_value = mock_client

            result = runner.invoke(app, ["--token", "tk", "campaigns", "stats", "--campaign-id", "1"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["total_delivered"] == 100
        assert data["opened"] == 50


class TestWebhooksCommands:
    def test_webhooks_smtp_get_outputs_webhook(self):
        from acumbamail.cli.main import app
        from acumbamail.models import SMTPWebhook

        mock_wh = SMTPWebhook(id=87492, url="https://example.com/wh", active=True,
                               delivered=True, hard_bounces=False, soft_bounces=False,
                               complaints=False, opens=False, clicks=False)
        with patch("acumbamail.cli.commands.webhooks.get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.get_smtp_webhook.return_value = mock_wh
            mock_get_client.return_value = mock_client

            result = runner.invoke(app, ["--token", "tk", "webhooks", "smtp-get"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == 87492
        assert data["active"] is True

    def test_webhooks_smtp_config_returns_id(self):
        from acumbamail.cli.main import app
        with patch("acumbamail.cli.commands.webhooks.get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.config_smtp_webhook.return_value = 87492
            mock_get_client.return_value = mock_client

            result = runner.invoke(app, [
                "--token", "tk", "webhooks", "smtp-config",
                "--url", "https://example.com/wh", "--delivered", "--active"
            ])

        assert result.exit_code == 0
        assert json.loads(result.output)["id"] == 87492

    def test_webhooks_list_get_outputs_webhook(self):
        from acumbamail.cli.main import app
        from acumbamail.models import ListWebhook

        mock_wh = ListWebhook(id=102650, url="https://example.com/wh", active=False,
                               subscribes=True, unsubscribes=True,
                               hard_bounces=False, soft_bounces=False,
                               complaints=False, opens=False, clicks=False)
        with patch("acumbamail.cli.commands.webhooks.get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.get_list_webhook.return_value = mock_wh
            mock_get_client.return_value = mock_client

            result = runner.invoke(app, ["--token", "tk", "webhooks", "list-get", "--list-id", "123"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == 102650
        assert data["subscribes"] is True

    def test_webhooks_list_config_returns_id(self):
        from acumbamail.cli.main import app
        with patch("acumbamail.cli.commands.webhooks.get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.config_list_webhook.return_value = 102650
            mock_get_client.return_value = mock_client

            result = runner.invoke(app, [
                "--token", "tk", "webhooks", "list-config",
                "--list-id", "123", "--url", "https://example.com/wh",
                "--subscribes", "--active"
            ])

        assert result.exit_code == 0
        assert json.loads(result.output)["id"] == 102650
