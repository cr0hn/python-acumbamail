"""Tests para los nuevos métodos del cliente síncrono."""
import json
import pytest
import httpx
from datetime import datetime
from pytest_httpx import HTTPXMock

from acumbamail import AcumbamailClient
from acumbamail.exceptions import AcumbamailValidationError
from acumbamail.models import (
    BatchSubscriberResult,
    InactiveSubscriber,
    ListWebhook,
    SMTPWebhook,
    SubscriberDetails,
    Template,
    Campaign,
)

TOKEN = "test_token"
LIST_ID = 1138335
BASE = "https://acumbamail.com/api/1"


@pytest.fixture
def client():
    return AcumbamailClient(
        auth_token=TOKEN,
        default_sender_name="Sender",
        default_sender_email="sender@test.com",
    )


def api_url(endpoint):
    return f"{BASE}/{endpoint}/"


# ---------------------------------------------------------------------------
# Subscribers
# ---------------------------------------------------------------------------

class TestAddMergeTag:
    def test_calls_api_with_correct_params(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("addMergeTag"), json={}, status_code=201)
        client.add_merge_tag(LIST_ID, "my_field", "text")
        request = httpx_mock.get_requests()[0]
        body = json.loads(request.content)
        assert body["list_id"] == LIST_ID
        assert body["field_name"] == "my_field"
        assert body["field_type"] == "text"

    def test_returns_none(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("addMergeTag"), json={}, status_code=201)
        result = client.add_merge_tag(LIST_ID, "field", "text")
        assert result is None


class TestBatchAddSubscribers:
    def test_returns_list_of_results(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("batchAddSubscribers"),
            json=[{"a@test.com": 111}, {"b@test.com": 222}],
            status_code=201,
        )
        results = client.batch_add_subscribers(
            LIST_ID,
            [{"email": "a@test.com"}, {"email": "b@test.com"}],
        )
        assert len(results) == 2
        assert isinstance(results[0], BatchSubscriberResult)
        assert results[0].email == "a@test.com"
        assert results[0].subscriber_id == 111
        assert results[1].email == "b@test.com"

    def test_sends_update_subscriber_flag(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("batchAddSubscribers"), json=[], status_code=201)
        client.batch_add_subscribers(LIST_ID, [], update_subscriber=True)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["update_subscriber"] == 1

    def test_update_subscriber_defaults_to_false(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("batchAddSubscribers"), json=[], status_code=201)
        client.batch_add_subscribers(LIST_ID, [])
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["update_subscriber"] == 0


class TestBatchDeleteSubscribers:
    def test_calls_api_with_email_list(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("batchDeleteSubscribers"), json={}, status_code=201)
        client.batch_delete_subscribers(LIST_ID, ["a@test.com", "b@test.com"])
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["list_id"] == LIST_ID
        assert body["email_list"] == ["a@test.com", "b@test.com"]


class TestDeleteAllSubscribers:
    def test_calls_api_with_list_id(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("deleteAllSubscribers"), json={}, status_code=201)
        client.delete_all_subscribers(LIST_ID)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["list_id"] == LIST_ID


class TestDeleteList:
    def test_calls_api_with_list_id(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("deleteList"), json={}, status_code=201)
        client.delete_list(LIST_ID)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["list_id"] == LIST_ID


class TestGetSmtpCredits:
    def test_returns_credits_as_int(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getCreditsSMTP"), json={"Creditos": 500000})
        credits = client.get_smtp_credits()
        assert credits == 500000

    def test_returns_zero_credits(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getCreditsSMTP"), json={"Creditos": 0})
        assert client.get_smtp_credits() == 0


class TestGetFields:
    def test_returns_field_dict(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getFields"),
            json={"email": "email", "-curso >a,b,c": "combobox"},
        )
        fields = client.get_fields(LIST_ID)
        assert fields["email"] == "email"
        assert fields["-curso >a,b,c"] == "combobox"


class TestGetForms:
    def test_returns_empty_dict_when_no_forms(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getForms"), json={})
        forms = client.get_forms(LIST_ID)
        assert forms == {}


class TestGetInactiveSubscribers:
    def test_returns_email_list_when_full_info_false(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getInactiveSubscribers"),
            json={"inactive_subscribers": [["a@test.com"], ["b@test.com"]]},
        )
        result = client.get_inactive_subscribers(
            datetime(2025, 1, 1), datetime(2025, 12, 31), full_info=False
        )
        assert result == ["a@test.com", "b@test.com"]

    def test_returns_inactive_subscriber_objects_when_full_info_true(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getInactiveSubscribers"),
            json={
                "inactive_subscribers": [
                    {"reason": 3, "reason_date": "2025/09/25 12:18:38", "email": "a@test.com"},
                ]
            },
        )
        result = client.get_inactive_subscribers(
            datetime(2025, 1, 1), datetime(2025, 12, 31), full_info=True
        )
        assert len(result) == 1
        assert isinstance(result[0], InactiveSubscriber)
        assert result[0].email == "a@test.com"
        assert result[0].reason == 3

    def test_sends_formatted_dates(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getInactiveSubscribers"), json={"inactive_subscribers": []})
        client.get_inactive_subscribers(datetime(2025, 3, 15), datetime(2025, 6, 30))
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["date_from"] == "2025-03-15"
        assert body["date_to"] == "2025-06-30"

    def test_returns_empty_list_when_no_inactive(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getInactiveSubscribers"), json={"inactive_subscribers": []})
        result = client.get_inactive_subscribers(datetime(2025, 1, 1), datetime(2025, 12, 31))
        assert result == []


class TestGetSubscriberDetails:
    def test_returns_subscriber_details(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getSubscriberDetails"),
            json={
                "cr0hn@cr0hn.com": {
                    "status": "active",
                    "create_date": "2025/06/30 07:32:30",
                    "email": "cr0hn@cr0hn.com",
                    "id": 5125884584,
                }
            },
        )
        details = client.get_subscriber_details(LIST_ID, "cr0hn@cr0hn.com")
        assert isinstance(details, SubscriberDetails)
        assert details.email == "cr0hn@cr0hn.com"
        assert details.id == 5125884584
        assert details.status == "active"


class TestSearchSubscriber:
    def test_returns_list_of_subscriber_details(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("searchSubscriber"),
            json=[
                {"status": "active", "create_date": "2025/06/30 07:32:30", "email": "cr0hn@cr0hn.com", "list_id": 1138335, "id": 5125884584}
            ],
        )
        results = client.search_subscriber("cr0hn@cr0hn.com")
        assert len(results) == 1
        assert isinstance(results[0], SubscriberDetails)
        assert results[0].email == "cr0hn@cr0hn.com"
        assert results[0].list_id == 1138335

    def test_returns_empty_list_when_not_found(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("searchSubscriber"), json=[])
        results = client.search_subscriber("nobody@nowhere.com")
        assert results == []


class TestUnsubscribeSubscriber:
    def test_calls_api_with_correct_params(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("unsubscribeSubscriber"), json={}, status_code=201)
        client.unsubscribe_subscriber(LIST_ID, "test@test.com")
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["list_id"] == LIST_ID
        assert body["email"] == "test@test.com"

    def test_returns_none(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("unsubscribeSubscriber"), json={}, status_code=201)
        result = client.unsubscribe_subscriber(LIST_ID, "test@test.com")
        assert result is None


# ---------------------------------------------------------------------------
# Campaigns
# ---------------------------------------------------------------------------

class TestSendTemplateCampaign:
    def test_returns_campaign_with_id(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("sendTemplateCampaign"), json=99999, status_code=201)
        campaign = client.send_template_campaign(
            name="Test",
            subject="Subject",
            template_id=8974913,
            list_ids=[LIST_ID],
        )
        assert isinstance(campaign, Campaign)
        assert campaign.id == 99999
        assert campaign.name == "Test"
        assert campaign.subject == "Subject"
        assert campaign.list_ids == [LIST_ID]

    def test_raises_when_no_from_email(self):
        c = AcumbamailClient(auth_token=TOKEN)
        with pytest.raises(AcumbamailValidationError):
            c.send_template_campaign("name", "subject", 123, [LIST_ID])

    def test_uses_default_sender_email(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("sendTemplateCampaign"), json=1, status_code=201)
        campaign = client.send_template_campaign("name", "subject", 123, [LIST_ID])
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["from_email"] == "sender@test.com"

    def test_sends_scheduled_at_when_provided(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("sendTemplateCampaign"), json=1, status_code=201)
        scheduled = datetime(2026, 1, 15, 10, 30)
        client.send_template_campaign("name", "subject", 123, [LIST_ID], scheduled_at=scheduled)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["date_send"] == "2026-01-15 10:30"

    def test_does_not_send_date_send_when_not_scheduled(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("sendTemplateCampaign"), json=1, status_code=201)
        client.send_template_campaign("name", "subject", 123, [LIST_ID])
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert "date_send" not in body


class TestDuplicateTemplate:
    def test_returns_template_with_new_id(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("duplicateTemplate"), json={"template_id": "9491649"})
        template = client.duplicate_template("SDK Copy", 8974913)
        assert isinstance(template, Template)
        assert template.id == 9491649
        assert template.name == "SDK Copy"

    def test_sends_correct_params(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("duplicateTemplate"), json={"template_id": "1"})
        client.duplicate_template("My Copy", 12345)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["template_name"] == "My Copy"
        assert body["origin_template_id"] == 12345


class TestGetCampaignOpenersByCountries:
    def test_returns_dict(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getCampaignOpenersByCountries"),
            json={"ES": 100, "US": 50},
        )
        result = client.get_campaign_openers_by_countries(999)
        assert result == {"ES": 100, "US": 50}


class TestGetTemplatesByName:
    def test_returns_list_of_templates(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getTemplatesByName"),
            json=[{"id": 1, "name": "My Template", "content": "<html/>"}],
        )
        templates = client.get_templates_by_name("My")
        assert len(templates) == 1
        assert isinstance(templates[0], Template)

    def test_returns_empty_list_when_api_returns_non_list(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getTemplatesByName"), json={})
        result = client.get_templates_by_name("nonexistent")
        assert result == []


# ---------------------------------------------------------------------------
# SMTP
# ---------------------------------------------------------------------------

class TestSendEmails:
    def test_sends_messages_and_returns_response(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("send"), json=["ok", "ok"])
        messages = [
            {"to_email": "a@test.com", "subject": "Hi", "body": "<p>Hi</p>"},
            {"to_email": "b@test.com", "subject": "Hi", "body": "<p>Hi</p>"},
        ]
        result = client.send_emails(messages)
        assert result == ["ok", "ok"]
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["messages"] == messages


class TestSendCertifiedEmail:
    def test_returns_response_as_string(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("sendCertifiedEmail"), json="certified_key_123")
        result = client.send_certified_email(
            to_email="recipient@test.com",
            subject="Certified",
            content="<p>Body</p>",
        )
        assert result == "certified_key_123"

    def test_raises_without_from_email(self):
        c = AcumbamailClient(auth_token=TOKEN)
        with pytest.raises(AcumbamailValidationError):
            c.send_certified_email("to@test.com", "subject", "body")

    def test_includes_cc_and_bcc_when_provided(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("sendCertifiedEmail"), json="key")
        client.send_certified_email(
            "to@test.com", "subject", "body",
            cc_email="cc@test.com",
            bcc_email="bcc@test.com",
        )
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["cc_email"] == "cc@test.com"
        assert body["bcc_email"] == "bcc@test.com"

    def test_does_not_include_cc_bcc_when_absent(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("sendCertifiedEmail"), json="key")
        client.send_certified_email("to@test.com", "subject", "body")
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert "cc_email" not in body
        assert "bcc_email" not in body


class TestGetEmailStatus:
    def test_returns_api_response(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getEmailStatus"),
            json={"status": "delivered", "opened": True},
        )
        result = client.get_email_status("key_abc123")
        assert result["status"] == "delivered"
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["email_key"] == "key_abc123"


# ---------------------------------------------------------------------------
# Webhooks
# ---------------------------------------------------------------------------

class TestGetSmtpWebhook:
    def test_returns_smtp_webhook_object(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getSMTPWebhook"),
            json={
                "info": {
                    "url": "https://example.com/wh",
                    "soft_bounces": False,
                    "complaints": False,
                    "delivered": True,
                    "active": True,
                    "hard_bounces": False,
                    "id": 87492,
                    "opens": False,
                    "clicks": False,
                }
            },
        )
        wh = client.get_smtp_webhook()
        assert isinstance(wh, SMTPWebhook)
        assert wh.id == 87492
        assert wh.url == "https://example.com/wh"
        assert wh.delivered is True
        assert wh.active is True


class TestGetListWebhook:
    def test_returns_list_webhook_object(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getListWebhook"),
            json={
                "info": {
                    "url": "https://example.com/wh",
                    "soft_bounces": False,
                    "complaints": False,
                    "unsubscribes": True,
                    "subscribes": True,
                    "active": False,
                    "hard_bounces": False,
                    "id": 102650,
                    "opens": False,
                    "clicks": False,
                }
            },
        )
        wh = client.get_list_webhook(LIST_ID)
        assert isinstance(wh, ListWebhook)
        assert wh.id == 102650
        assert wh.subscribes is True
        assert wh.unsubscribes is True


class TestConfigSmtpWebhook:
    def test_returns_webhook_id(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("configSMTPWebhook"), json={"id": 87492})
        result = client.config_smtp_webhook("https://example.com/wh", delivered=True, active=True)
        assert result == 87492

    def test_converts_bools_to_int_flags(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("configSMTPWebhook"), json={"id": 1})
        client.config_smtp_webhook(
            "https://example.com/wh",
            delivered=True,
            hard_bounce=True,
            soft_bounce=False,
            complain=False,
            opens=True,
            click=False,
            active=True,
        )
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["delivered"] == 1
        assert body["hard_bounce"] == 1
        assert body["soft_bounce"] == 0
        assert body["opens"] == 1
        assert body["active"] == 1


class TestConfigListWebhook:
    def test_returns_webhook_id(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("configListWebhook"), json={"id": 102650})
        result = client.config_list_webhook(LIST_ID, "https://example.com/wh", subscribes=True)
        assert result == 102650

    def test_sends_list_id_and_all_flags(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("configListWebhook"), json={"id": 1})
        client.config_list_webhook(
            LIST_ID,
            "https://example.com/wh",
            subscribes=True,
            unsubscribes=True,
            active=False,
        )
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["list_id"] == LIST_ID
        assert body["subscribes"] == 1
        assert body["unsubscribes"] == 1
        assert body["active"] == 0


# ---------------------------------------------------------------------------
# New parameter tests
# ---------------------------------------------------------------------------

class TestAddSubscriberNewParams:
    def test_sends_double_optin_flag(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("addSubscriber"), json=123, status_code=201)
        client.add_subscriber("x@test.com", 123, double_optin=True)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["double_optin"] == 1

    def test_double_optin_defaults_to_false(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("addSubscriber"), json=123, status_code=201)
        client.add_subscriber("x@test.com", 123)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["double_optin"] == 0

    def test_sends_update_subscriber_flag(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("addSubscriber"), json=123, status_code=201)
        client.add_subscriber("x@test.com", 123, update_subscriber=True)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["update_subscriber"] == 1

    def test_update_subscriber_defaults_to_false(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("addSubscriber"), json=123, status_code=201)
        client.add_subscriber("x@test.com", 123)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["update_subscriber"] == 0


class TestGetSubscribersNewParams:
    def test_sends_block_index(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getSubscribers"), json={})
        client.get_subscribers(123, block_index=2)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["block_index"] == 2

    def test_block_index_defaults_to_zero(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getSubscribers"), json={})
        client.get_subscribers(123)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["block_index"] == 0

    def test_sends_all_fields_flag(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getSubscribers"), json={})
        client.get_subscribers(123, all_fields=True)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["all_fields"] == 1

    def test_all_fields_defaults_to_false(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getSubscribers"), json={})
        client.get_subscribers(123)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["all_fields"] == 0

    def test_sends_complete_json_flag(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getSubscribers"), json={})
        client.get_subscribers(123, complete_json=True)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["complete_json"] == 1


class TestGetListSubsStatsNewParams:
    def test_sends_block_index(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getListSubsStats"), json={})
        client.get_list_subs_stats(123, block_index=3)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["block_index"] == 3

    def test_block_index_defaults_to_zero(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getListSubsStats"), json={})
        client.get_list_subs_stats(123)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["block_index"] == 0
