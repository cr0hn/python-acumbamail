"""Tests para los nuevos métodos del cliente asíncrono."""
import json
import pytest
import pytest_asyncio
from datetime import datetime
from pytest_httpx import HTTPXMock

from acumbamail import AsyncAcumbamailClient
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

pytestmark = pytest.mark.asyncio

TOKEN = "test_token"
LIST_ID = 1138335
BASE = "https://acumbamail.com/api/1"


@pytest_asyncio.fixture
async def async_client():
    async with AsyncAcumbamailClient(
        auth_token=TOKEN,
        default_sender_name="Sender",
        default_sender_email="sender@test.com",
    ) as client:
        yield client


def api_url(endpoint):
    return f"{BASE}/{endpoint}/"


# ---------------------------------------------------------------------------
# Subscribers
# ---------------------------------------------------------------------------

class TestAddMergeTag:
    async def test_calls_api_with_correct_params(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("addMergeTag"), json={}, status_code=201)
        await async_client.add_merge_tag(LIST_ID, "my_field", "text")
        request = httpx_mock.get_requests()[0]
        body = json.loads(request.content)
        assert body["list_id"] == LIST_ID
        assert body["field_name"] == "my_field"
        assert body["field_type"] == "text"

    async def test_returns_none(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("addMergeTag"), json={}, status_code=201)
        result = await async_client.add_merge_tag(LIST_ID, "field", "text")
        assert result is None


class TestBatchAddSubscribers:
    async def test_returns_list_of_results(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("batchAddSubscribers"),
            json=[{"a@test.com": 111}, {"b@test.com": 222}],
            status_code=201,
        )
        results = await async_client.batch_add_subscribers(
            LIST_ID,
            [{"email": "a@test.com"}, {"email": "b@test.com"}],
        )
        assert len(results) == 2
        assert isinstance(results[0], BatchSubscriberResult)
        assert results[0].email == "a@test.com"
        assert results[0].subscriber_id == 111
        assert results[1].email == "b@test.com"

    async def test_sends_update_subscriber_flag(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("batchAddSubscribers"), json=[], status_code=201)
        await async_client.batch_add_subscribers(LIST_ID, [], update_subscriber=True)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["update_subscriber"] == 1

    async def test_update_subscriber_defaults_to_false(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("batchAddSubscribers"), json=[], status_code=201)
        await async_client.batch_add_subscribers(LIST_ID, [])
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["update_subscriber"] == 0


class TestBatchDeleteSubscribers:
    async def test_calls_api_with_email_list(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("batchDeleteSubscribers"), json={}, status_code=201)
        await async_client.batch_delete_subscribers(LIST_ID, ["a@test.com", "b@test.com"])
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["list_id"] == LIST_ID
        assert body["email_list"] == ["a@test.com", "b@test.com"]


class TestDeleteAllSubscribers:
    async def test_calls_api_with_list_id(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("deleteAllSubscribers"), json={}, status_code=201)
        await async_client.delete_all_subscribers(LIST_ID)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["list_id"] == LIST_ID


class TestDeleteList:
    async def test_calls_api_with_list_id(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("deleteList"), json={}, status_code=201)
        await async_client.delete_list(LIST_ID)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["list_id"] == LIST_ID


class TestGetSmtpCredits:
    async def test_returns_credits_as_int(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getCreditsSMTP"), json={"Creditos": 500000})
        credits = await async_client.get_smtp_credits()
        assert credits == 500000

    async def test_returns_zero_credits(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getCreditsSMTP"), json={"Creditos": 0})
        assert await async_client.get_smtp_credits() == 0


class TestGetFields:
    async def test_returns_field_dict(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getFields"),
            json={"email": "email", "-curso >a,b,c": "combobox"},
        )
        fields = await async_client.get_fields(LIST_ID)
        assert fields["email"] == "email"
        assert fields["-curso >a,b,c"] == "combobox"


class TestGetForms:
    async def test_returns_empty_dict_when_no_forms(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getForms"), json={})
        forms = await async_client.get_forms(LIST_ID)
        assert forms == {}


class TestGetInactiveSubscribers:
    async def test_returns_email_list_when_full_info_false(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getInactiveSubscribers"),
            json={"inactive_subscribers": [["a@test.com"], ["b@test.com"]]},
        )
        result = await async_client.get_inactive_subscribers(
            datetime(2025, 1, 1), datetime(2025, 12, 31), full_info=False
        )
        assert result == ["a@test.com", "b@test.com"]

    async def test_returns_inactive_subscriber_objects_when_full_info_true(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getInactiveSubscribers"),
            json={
                "inactive_subscribers": [
                    {"reason": 3, "reason_date": "2025/09/25 12:18:38", "email": "a@test.com"},
                ]
            },
        )
        result = await async_client.get_inactive_subscribers(
            datetime(2025, 1, 1), datetime(2025, 12, 31), full_info=True
        )
        assert len(result) == 1
        assert isinstance(result[0], InactiveSubscriber)
        assert result[0].email == "a@test.com"
        assert result[0].reason == 3

    async def test_sends_formatted_dates(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getInactiveSubscribers"), json={"inactive_subscribers": []})
        await async_client.get_inactive_subscribers(datetime(2025, 3, 15), datetime(2025, 6, 30))
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["date_from"] == "2025-03-15"
        assert body["date_to"] == "2025-06-30"

    async def test_returns_empty_list_when_no_inactive(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getInactiveSubscribers"), json={"inactive_subscribers": []})
        result = await async_client.get_inactive_subscribers(datetime(2025, 1, 1), datetime(2025, 12, 31))
        assert result == []


class TestGetSubscriberDetails:
    async def test_returns_subscriber_details(self, async_client, httpx_mock: HTTPXMock):
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
        details = await async_client.get_subscriber_details(LIST_ID, "cr0hn@cr0hn.com")
        assert isinstance(details, SubscriberDetails)
        assert details.email == "cr0hn@cr0hn.com"
        assert details.id == 5125884584
        assert details.status == "active"


class TestSearchSubscriber:
    async def test_returns_list_of_subscriber_details(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("searchSubscriber"),
            json=[
                {"status": "active", "create_date": "2025/06/30 07:32:30", "email": "cr0hn@cr0hn.com", "list_id": 1138335, "id": 5125884584}
            ],
        )
        results = await async_client.search_subscriber("cr0hn@cr0hn.com")
        assert len(results) == 1
        assert isinstance(results[0], SubscriberDetails)
        assert results[0].email == "cr0hn@cr0hn.com"
        assert results[0].list_id == 1138335

    async def test_returns_empty_list_when_not_found(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("searchSubscriber"), json=[])
        results = await async_client.search_subscriber("nobody@nowhere.com")
        assert results == []


class TestUnsubscribeSubscriber:
    async def test_calls_api_with_correct_params(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("unsubscribeSubscriber"), json={}, status_code=201)
        await async_client.unsubscribe_subscriber(LIST_ID, "test@test.com")
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["list_id"] == LIST_ID
        assert body["email"] == "test@test.com"

    async def test_returns_none(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("unsubscribeSubscriber"), json={}, status_code=201)
        result = await async_client.unsubscribe_subscriber(LIST_ID, "test@test.com")
        assert result is None


# ---------------------------------------------------------------------------
# Campaigns
# ---------------------------------------------------------------------------

class TestSendTemplateCampaign:
    async def test_returns_campaign_with_id(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("sendTemplateCampaign"), json=99999, status_code=201)
        campaign = await async_client.send_template_campaign(
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

    async def test_raises_when_no_from_email(self):
        async with AsyncAcumbamailClient(auth_token=TOKEN) as c:
            with pytest.raises(AcumbamailValidationError):
                await c.send_template_campaign("name", "subject", 123, [LIST_ID])

    async def test_uses_default_sender_email(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("sendTemplateCampaign"), json=1, status_code=201)
        await async_client.send_template_campaign("name", "subject", 123, [LIST_ID])
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["from_email"] == "sender@test.com"

    async def test_sends_scheduled_at_when_provided(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("sendTemplateCampaign"), json=1, status_code=201)
        scheduled = datetime(2026, 1, 15, 10, 30)
        await async_client.send_template_campaign("name", "subject", 123, [LIST_ID], scheduled_at=scheduled)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["date_send"] == "2026-01-15 10:30"

    async def test_does_not_send_date_send_when_not_scheduled(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("sendTemplateCampaign"), json=1, status_code=201)
        await async_client.send_template_campaign("name", "subject", 123, [LIST_ID])
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert "date_send" not in body


class TestDuplicateTemplate:
    async def test_returns_template_with_new_id(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("duplicateTemplate"), json={"template_id": "9491649"})
        template = await async_client.duplicate_template("SDK Copy", 8974913)
        assert isinstance(template, Template)
        assert template.id == 9491649
        assert template.name == "SDK Copy"

    async def test_sends_correct_params(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("duplicateTemplate"), json={"template_id": "1"})
        await async_client.duplicate_template("My Copy", 12345)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["template_name"] == "My Copy"
        assert body["origin_template_id"] == 12345


class TestGetCampaignOpenersByCountries:
    async def test_returns_dict(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getCampaignOpenersByCountries"),
            json={"ES": 100, "US": 50},
        )
        result = await async_client.get_campaign_openers_by_countries(999)
        assert result == {"ES": 100, "US": 50}


class TestGetTemplatesByName:
    async def test_returns_list_of_templates(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getTemplatesByName"),
            json=[{"id": 1, "name": "My Template", "content": "<html/>"}],
        )
        templates = await async_client.get_templates_by_name("My")
        assert len(templates) == 1
        assert isinstance(templates[0], Template)

    async def test_returns_empty_list_when_api_returns_non_list(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getTemplatesByName"), json={})
        result = await async_client.get_templates_by_name("nonexistent")
        assert result == []

    async def test_emits_user_warning(self, async_client, httpx_mock: HTTPXMock):
        import warnings
        httpx_mock.add_response(url=api_url("getTemplatesByName"), json=[])
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            await async_client.get_templates_by_name("test")
            assert len(w) == 1
            assert issubclass(w[0].category, UserWarning)
            assert "no implementado" in str(w[0].message).lower() or "404" in str(w[0].message)


# ---------------------------------------------------------------------------
# SMTP
# ---------------------------------------------------------------------------

class TestSendEmails:
    async def test_sends_messages_and_returns_response(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("send"), json=["ok", "ok"])
        messages = [
            {"to_email": "a@test.com", "subject": "Hi", "body": "<p>Hi</p>"},
            {"to_email": "b@test.com", "subject": "Hi", "body": "<p>Hi</p>"},
        ]
        result = await async_client.send_emails(messages)
        assert result == ["ok", "ok"]
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["messages"] == messages


class TestSendCertifiedEmail:
    async def test_returns_response_as_string(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("sendCertifiedEmail"), json="certified_key_123")
        result = await async_client.send_certified_email(
            to_email="recipient@test.com",
            subject="Certified",
            content="<p>Body</p>",
        )
        assert result == "certified_key_123"

    async def test_raises_without_from_email(self):
        async with AsyncAcumbamailClient(auth_token=TOKEN) as c:
            with pytest.raises(AcumbamailValidationError):
                await c.send_certified_email("to@test.com", "subject", "body")

    async def test_includes_cc_and_bcc_when_provided(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("sendCertifiedEmail"), json="key")
        await async_client.send_certified_email(
            "to@test.com", "subject", "body",
            cc_email="cc@test.com",
            bcc_email="bcc@test.com",
        )
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["cc_email"] == "cc@test.com"
        assert body["bcc_email"] == "bcc@test.com"

    async def test_does_not_include_cc_bcc_when_absent(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("sendCertifiedEmail"), json="key")
        await async_client.send_certified_email("to@test.com", "subject", "body")
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert "cc_email" not in body
        assert "bcc_email" not in body


class TestGetEmailStatus:
    async def test_returns_api_response(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getEmailStatus"),
            json={"status": "delivered", "opened": True},
        )
        result = await async_client.get_email_status("key_abc123")
        assert result["status"] == "delivered"
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["email_key"] == "key_abc123"


# ---------------------------------------------------------------------------
# Webhooks
# ---------------------------------------------------------------------------

class TestGetSmtpWebhook:
    async def test_returns_smtp_webhook_object(self, async_client, httpx_mock: HTTPXMock):
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
        wh = await async_client.get_smtp_webhook()
        assert isinstance(wh, SMTPWebhook)
        assert wh.id == 87492
        assert wh.url == "https://example.com/wh"
        assert wh.delivered is True
        assert wh.active is True


class TestGetListWebhook:
    async def test_returns_list_webhook_object(self, async_client, httpx_mock: HTTPXMock):
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
        wh = await async_client.get_list_webhook(LIST_ID)
        assert isinstance(wh, ListWebhook)
        assert wh.id == 102650
        assert wh.subscribes is True
        assert wh.unsubscribes is True


class TestConfigSmtpWebhook:
    async def test_returns_webhook_id(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("configSMTPWebhook"), json={"id": 87492})
        result = await async_client.config_smtp_webhook("https://example.com/wh", delivered=True, active=True)
        assert result == 87492

    async def test_converts_bools_to_int_flags(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("configSMTPWebhook"), json={"id": 1})
        await async_client.config_smtp_webhook(
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
    async def test_returns_webhook_id(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("configListWebhook"), json={"id": 102650})
        result = await async_client.config_list_webhook(LIST_ID, "https://example.com/wh", subscribes=True)
        assert result == 102650

    async def test_sends_list_id_and_all_flags(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("configListWebhook"), json={"id": 1})
        await async_client.config_list_webhook(
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
    async def test_sends_double_optin_flag(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("addSubscriber"), json=123, status_code=201)
        await async_client.add_subscriber("x@test.com", 123, double_optin=True)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["double_optin"] == 1

    async def test_double_optin_defaults_to_false(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("addSubscriber"), json=123, status_code=201)
        await async_client.add_subscriber("x@test.com", 123)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["double_optin"] == 0

    async def test_sends_update_subscriber_flag(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("addSubscriber"), json=123, status_code=201)
        await async_client.add_subscriber("x@test.com", 123, update_subscriber=True)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["update_subscriber"] == 1

    async def test_update_subscriber_defaults_to_false(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("addSubscriber"), json=123, status_code=201)
        await async_client.add_subscriber("x@test.com", 123)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["update_subscriber"] == 0


class TestGetSubscribersNewParams:
    async def test_sends_block_index(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getSubscribers"), json={})
        await async_client.get_subscribers(123, block_index=2)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["block_index"] == 2

    async def test_block_index_defaults_to_zero(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getSubscribers"), json={})
        await async_client.get_subscribers(123)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["block_index"] == 0

    async def test_sends_all_fields_flag(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getSubscribers"), json={})
        await async_client.get_subscribers(123, all_fields=True)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["all_fields"] == 1

    async def test_all_fields_defaults_to_false(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getSubscribers"), json={})
        await async_client.get_subscribers(123)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["all_fields"] == 0

    async def test_sends_complete_json_flag(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getSubscribers"), json={})
        await async_client.get_subscribers(123, complete_json=True)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["complete_json"] == 1


class TestGetListSubsStatsNewParams:
    async def test_sends_block_index(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getListSubsStats"), json={})
        await async_client.get_list_subs_stats(123, block_index=3)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["block_index"] == 3

    async def test_block_index_defaults_to_zero(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getListSubsStats"), json={})
        await async_client.get_list_subs_stats(123)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["block_index"] == 0
