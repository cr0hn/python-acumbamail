"""Tests para los métodos originales (pre-sesión) del cliente asíncrono."""
import json
import pytest
import pytest_asyncio
from datetime import datetime
from pytest_httpx import HTTPXMock

from acumbamail import AsyncAcumbamailClient
from acumbamail.exceptions import AcumbamailValidationError
from acumbamail.models import (
    MailList,
    Subscriber,
    Campaign,
    CampaignClick,
    CampaignOpener,
    CampaignSoftBounce,
    CampaignTotalInformation,
    Template,
)

pytestmark = pytest.mark.asyncio

TOKEN = "test_token"
LIST_ID = 1138335
CAMPAIGN_ID = 999
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
# Lists
# ---------------------------------------------------------------------------

class TestGetLists:
    async def test_returns_list_of_mail_lists(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getLists"),
            json={"1138335": {"name": "Newsletter", "description": ""}},
        )
        httpx_mock.add_response(
            url=api_url("getListStats"),
            json={
                "total_subscribers": 9,
                "unsubscribed_subscribers": 0,
                "hard_bounced_subscribers": 0,
                "campaigns_sent": 5,
            },
        )
        result = await async_client.get_lists()
        assert len(result) == 1
        assert isinstance(result[0], MailList)
        assert result[0].id == 1138335
        assert result[0].name == "Newsletter"
        assert result[0].subscribers_count == 9

    async def test_calls_get_list_stats_for_each_list(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getLists"),
            json={
                "111": {"name": "List A", "description": ""},
                "222": {"name": "List B", "description": ""},
            },
        )
        httpx_mock.add_response(
            url=api_url("getListStats"),
            json={"total_subscribers": 5, "unsubscribed_subscribers": 0, "hard_bounced_subscribers": 0},
        )
        httpx_mock.add_response(
            url=api_url("getListStats"),
            json={"total_subscribers": 10, "unsubscribed_subscribers": 1, "hard_bounced_subscribers": 0},
        )
        result = await async_client.get_lists()
        assert len(result) == 2

    async def test_returns_empty_list_when_no_lists(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getLists"), json={})
        result = await async_client.get_lists()
        assert result == []

    async def test_mail_list_has_bounce_count(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getLists"),
            json={"1138335": {"name": "Newsletter", "description": ""}},
        )
        httpx_mock.add_response(
            url=api_url("getListStats"),
            json={
                "total_subscribers": 9,
                "unsubscribed_subscribers": 2,
                "hard_bounced_subscribers": 3,
            },
        )
        result = await async_client.get_lists()
        assert result[0].bounced_count == 3
        assert result[0].unsubscribed_count == 2


class TestCreateList:
    async def test_returns_mail_list_with_id(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("createList"), json=456, status_code=201)
        result = await async_client.create_list("My Newsletter")
        assert isinstance(result, MailList)
        assert result.id == 456
        assert result.name == "My Newsletter"

    async def test_raises_when_no_default_sender_email(self):
        async with AsyncAcumbamailClient(auth_token=TOKEN) as c:
            with pytest.raises(AcumbamailValidationError):
                await c.create_list("My List")

    async def test_raises_when_name_is_empty(self, async_client):
        with pytest.raises(AcumbamailValidationError):
            await async_client.create_list("")

    async def test_raises_when_name_is_whitespace(self, async_client):
        with pytest.raises(AcumbamailValidationError):
            await async_client.create_list("   ")

    async def test_sends_sender_email_from_default(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("createList"), json=456, status_code=201)
        await async_client.create_list("My List")
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["sender_email"] == "sender@test.com"

    async def test_sends_name_and_description(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("createList"), json=456, status_code=201)
        await async_client.create_list("My List", description="A description")
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["name"] == "My List"
        assert body["description"] == "A description"

    async def test_includes_company_when_set(self, httpx_mock: HTTPXMock):
        async with AsyncAcumbamailClient(
            auth_token=TOKEN,
            default_sender_email="x@x.com",
            sender_company="Acme Inc",
        ) as c:
            httpx_mock.add_response(url=api_url("createList"), json=1, status_code=201)
            await c.create_list("List")
            body = json.loads(httpx_mock.get_requests()[0].content)
            assert body["company"] == "Acme Inc"


class TestGetSubscribers:
    async def test_returns_list_of_subscribers(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getSubscribers"),
            json={"test@test.com": {"status": "active", "id": 5678, "email": "test@test.com"}},
        )
        result = await async_client.get_subscribers(LIST_ID)
        assert len(result) == 1
        assert isinstance(result[0], Subscriber)
        assert result[0].email == "test@test.com"
        assert result[0].list_id == LIST_ID

    async def test_returns_empty_list_when_no_subscribers(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getSubscribers"), json={})
        result = await async_client.get_subscribers(LIST_ID)
        assert result == []

    async def test_sends_list_id(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getSubscribers"), json={})
        await async_client.get_subscribers(LIST_ID)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["list_id"] == LIST_ID


class TestAddSubscriber:
    async def test_returns_subscriber_object(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("addSubscriber"), json=5678, status_code=201)
        result = await async_client.add_subscriber("user@test.com", LIST_ID)
        assert isinstance(result, Subscriber)
        assert result.email == "user@test.com"
        assert result.list_id == LIST_ID

    async def test_raises_when_email_invalid(self, async_client):
        with pytest.raises(AcumbamailValidationError):
            await async_client.add_subscriber("notanemail", LIST_ID)

    async def test_raises_when_email_empty(self, async_client):
        with pytest.raises(AcumbamailValidationError):
            await async_client.add_subscriber("", LIST_ID)

    async def test_sends_email_in_merge_fields(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("addSubscriber"), json=5678, status_code=201)
        await async_client.add_subscriber("user@test.com", LIST_ID)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["list_id"] == LIST_ID
        assert body["merge_fields"]["email"] == "user@test.com"

    async def test_includes_custom_fields(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("addSubscriber"), json=5678, status_code=201)
        await async_client.add_subscriber("user@test.com", LIST_ID, fields={"name": "John"})
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["merge_fields"]["name"] == "John"

    async def test_lowercases_email(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("addSubscriber"), json=5678, status_code=201)
        result = await async_client.add_subscriber("USER@TEST.COM", LIST_ID)
        assert result.email == "user@test.com"


class TestDeleteSubscriber:
    async def test_calls_api_with_correct_params(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("deleteSubscriber"),
            json={"email": "test@test.com"},
            status_code=201,
        )
        await async_client.delete_subscriber("test@test.com", LIST_ID)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["list_id"] == LIST_ID
        assert body["email"] == "test@test.com"

    async def test_raises_when_email_invalid(self, async_client):
        with pytest.raises(AcumbamailValidationError):
            await async_client.delete_subscriber("notanemail", LIST_ID)

    async def test_raises_when_email_empty(self, async_client):
        with pytest.raises(AcumbamailValidationError):
            await async_client.delete_subscriber("", LIST_ID)

    async def test_returns_none(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("deleteSubscriber"),
            json={"email": "test@test.com"},
            status_code=201,
        )
        result = await async_client.delete_subscriber("test@test.com", LIST_ID)
        assert result is None


class TestGetListStats:
    async def test_returns_stats_dict(self, async_client, httpx_mock: HTTPXMock):
        stats = {
            "total_subscribers": 9,
            "unsubscribed_subscribers": 0,
            "hard_bounced_subscribers": 0,
            "campaigns_sent": 5,
        }
        httpx_mock.add_response(url=api_url("getListStats"), json=stats)
        result = await async_client.get_list_stats(LIST_ID)
        assert result["total_subscribers"] == 9
        assert result["campaigns_sent"] == 5

    async def test_sends_list_id(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getListStats"), json={})
        await async_client.get_list_stats(LIST_ID)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["list_id"] == LIST_ID


class TestGetListFields:
    async def test_returns_api_response(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getListFields"),
            json=[{"name": "email", "type": "email"}],
        )
        result = await async_client.get_list_fields(LIST_ID)
        assert result == [{"name": "email", "type": "email"}]

    async def test_sends_list_id(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getListFields"), json=[])
        await async_client.get_list_fields(LIST_ID)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["list_id"] == LIST_ID


class TestGetListSegments:
    async def test_returns_api_response(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getListSegments"),
            json=[{"id": 1, "name": "Segment A"}],
        )
        result = await async_client.get_list_segments(LIST_ID)
        assert result == [{"id": 1, "name": "Segment A"}]

    async def test_sends_list_id(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getListSegments"), json=[])
        await async_client.get_list_segments(LIST_ID)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["list_id"] == LIST_ID


class TestGetListSubsStats:
    async def test_returns_stats_dict(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getListSubsStats"),
            json={"active": 100, "unsubscribed": 5},
        )
        result = await async_client.get_list_subs_stats(LIST_ID)
        assert result == {"active": 100, "unsubscribed": 5}

    async def test_sends_list_id(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getListSubsStats"), json={})
        await async_client.get_list_subs_stats(LIST_ID)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["list_id"] == LIST_ID


class TestGetMergeFields:
    async def test_returns_api_response(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getMergeFields"),
            json=[{"field_name": "nombre", "field_type": "text"}],
        )
        result = await async_client.get_merge_fields(LIST_ID)
        assert result == [{"field_name": "nombre", "field_type": "text"}]

    async def test_sends_list_id(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getMergeFields"), json=[])
        await async_client.get_merge_fields(LIST_ID)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["list_id"] == LIST_ID


# ---------------------------------------------------------------------------
# Campaigns
# ---------------------------------------------------------------------------

UNSUBSCRIBE_CONTENT = "<p>Hello *|UNSUBSCRIBE_URL|*</p>"


class TestCreateCampaign:
    async def test_returns_campaign_with_id(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("createCampaign"), json=99, status_code=201)
        campaign = await async_client.create_campaign(
            name="My Campaign",
            subject="Subject",
            content=UNSUBSCRIBE_CONTENT,
            list_ids=[LIST_ID],
        )
        assert isinstance(campaign, Campaign)
        assert campaign.id == 99
        assert campaign.name == "My Campaign"
        assert campaign.subject == "Subject"
        assert campaign.list_ids == [LIST_ID]

    async def test_raises_when_no_from_email(self):
        async with AsyncAcumbamailClient(auth_token=TOKEN) as c:
            with pytest.raises(AcumbamailValidationError):
                await c.create_campaign("name", "subj", UNSUBSCRIBE_CONTENT, [LIST_ID])

    async def test_raises_when_content_missing_unsubscribe_url(self, async_client):
        with pytest.raises(AcumbamailValidationError):
            await async_client.create_campaign("name", "subj", "<p>No unsubscribe link</p>", [LIST_ID])

    async def test_raises_when_list_ids_is_empty(self, async_client):
        with pytest.raises(AcumbamailValidationError):
            await async_client.create_campaign("name", "subj", UNSUBSCRIBE_CONTENT, [])

    async def test_uses_default_sender_email(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("createCampaign"), json=1, status_code=201)
        await async_client.create_campaign("name", "subj", UNSUBSCRIBE_CONTENT, [LIST_ID])
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["from_email"] == "sender@test.com"

    async def test_overrides_from_email_when_provided(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("createCampaign"), json=1, status_code=201)
        await async_client.create_campaign(
            "name", "subj", UNSUBSCRIBE_CONTENT, [LIST_ID],
            from_email="other@test.com",
        )
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["from_email"] == "other@test.com"

    async def test_includes_scheduled_at_when_provided(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("createCampaign"), json=1, status_code=201)
        scheduled = datetime(2026, 3, 15, 9, 0)
        await async_client.create_campaign(
            "name", "subj", UNSUBSCRIBE_CONTENT, [LIST_ID],
            scheduled_at=scheduled,
        )
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["date_send"] == "2026-03-15 09:00"

    async def test_does_not_include_date_send_when_not_scheduled(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("createCampaign"), json=1, status_code=201)
        await async_client.create_campaign("name", "subj", UNSUBSCRIBE_CONTENT, [LIST_ID])
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert "date_send" not in body


class TestSendSingleEmail:
    async def test_returns_email_id(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("sendOne"), json=5678)
        result = await async_client.send_single_email(
            to_email="to@test.com",
            subject="Hello",
            content="<p>Body</p>",
        )
        assert result == 5678

    async def test_raises_when_no_from_email(self):
        async with AsyncAcumbamailClient(auth_token=TOKEN) as c:
            with pytest.raises(AcumbamailValidationError):
                await c.send_single_email("to@test.com", "subj", "body")

    async def test_sends_correct_params(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("sendOne"), json=1)
        await async_client.send_single_email(
            to_email="to@test.com",
            subject="Hello",
            content="<p>Body</p>",
        )
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["to_email"] == "to@test.com"
        assert body["subject"] == "Hello"
        assert body["body"] == "<p>Body</p>"
        assert body["from_email"] == "sender@test.com"


class TestGetCampaignBasicInformation:
    async def test_returns_api_response(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getCampaignBasicInformation"),
            json={"name": "Camp1", "subject": "Subj"},
        )
        result = await async_client.get_campaign_basic_information(CAMPAIGN_ID)
        assert result["name"] == "Camp1"
        assert result["subject"] == "Subj"

    async def test_sends_campaign_id(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getCampaignBasicInformation"), json={})
        await async_client.get_campaign_basic_information(CAMPAIGN_ID)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["campaign_id"] == CAMPAIGN_ID


class TestGetCampaignClicks:
    async def test_returns_list_of_campaign_clicks(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getCampaignClicks"),
            json=[{
                "url": "https://x.com",
                "clicks": 10,
                "unique_clicks": 8,
                "click_rate": 0.1,
                "unique_click_rate": 0.08,
            }],
        )
        result = await async_client.get_campaign_clicks(CAMPAIGN_ID)
        assert len(result) == 1
        assert isinstance(result[0], CampaignClick)
        assert result[0].url == "https://x.com"
        assert result[0].clicks == 10
        assert result[0].unique_clicks == 8

    async def test_returns_empty_list_when_no_clicks(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getCampaignClicks"), json=[])
        result = await async_client.get_campaign_clicks(CAMPAIGN_ID)
        assert result == []

    async def test_sends_campaign_id(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getCampaignClicks"), json=[])
        await async_client.get_campaign_clicks(CAMPAIGN_ID)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["campaign_id"] == CAMPAIGN_ID


class TestGetCampaignInformationByISP:
    async def test_returns_dict(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getCampaignInformationByISP"),
            json={"Gmail": {"sent": 50, "opened": 20}},
        )
        result = await async_client.get_campaign_information_by_isp(CAMPAIGN_ID)
        assert result["Gmail"]["sent"] == 50

    async def test_sends_campaign_id(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getCampaignInformationByISP"), json={})
        await async_client.get_campaign_information_by_isp(CAMPAIGN_ID)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["campaign_id"] == CAMPAIGN_ID


class TestGetCampaignLinks:
    async def test_returns_list_of_links(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getCampaignLinks"),
            json=["https://a.com", "https://b.com"],
        )
        result = await async_client.get_campaign_links(CAMPAIGN_ID)
        assert result == ["https://a.com", "https://b.com"]

    async def test_sends_campaign_id(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getCampaignLinks"), json=[])
        await async_client.get_campaign_links(CAMPAIGN_ID)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["campaign_id"] == CAMPAIGN_ID


class TestGetCampaignOpeners:
    async def test_returns_list_of_campaign_openers(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getCampaignOpeners"),
            json=[{"email": "u@x.com", "opened_at": "2025-01-01T10:00:00"}],
        )
        result = await async_client.get_campaign_openers(CAMPAIGN_ID)
        assert len(result) == 1
        assert isinstance(result[0], CampaignOpener)
        assert result[0].email == "u@x.com"

    async def test_returns_empty_list_when_no_openers(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getCampaignOpeners"), json=[])
        result = await async_client.get_campaign_openers(CAMPAIGN_ID)
        assert result == []

    async def test_sends_campaign_id(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getCampaignOpeners"), json=[])
        await async_client.get_campaign_openers(CAMPAIGN_ID)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["campaign_id"] == CAMPAIGN_ID


class TestGetCampaignOpenersByBrowser:
    async def test_returns_dict(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getCampaignOpenersByBrowser"),
            json={"Chrome": 50, "Firefox": 10},
        )
        result = await async_client.get_campaign_openers_by_browser(CAMPAIGN_ID)
        assert result == {"Chrome": 50, "Firefox": 10}

    async def test_sends_campaign_id(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getCampaignOpenersByBrowser"), json={})
        await async_client.get_campaign_openers_by_browser(CAMPAIGN_ID)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["campaign_id"] == CAMPAIGN_ID


class TestGetCampaignOpenersByOs:
    async def test_returns_dict(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getCampaignOpenersByOs"),
            json={"macOS": 30, "Windows": 20},
        )
        result = await async_client.get_campaign_openers_by_os(CAMPAIGN_ID)
        assert result == {"macOS": 30, "Windows": 20}

    async def test_sends_campaign_id(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getCampaignOpenersByOs"), json={})
        await async_client.get_campaign_openers_by_os(CAMPAIGN_ID)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["campaign_id"] == CAMPAIGN_ID


class TestGetCampaigns:
    async def test_returns_list_of_campaigns(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getCampaigns"),
            json=[{
                "id": 1,
                "name": "Camp1",
                "subject": "Subj",
                "content": "<p>test *|UNSUBSCRIBE_URL|*</p>",
                "from_name": "Sender",
                "from_email": "sender@test.com",
                "lists": [LIST_ID],
            }],
        )
        result = await async_client.get_campaigns(complete_json=True)
        assert len(result) == 1
        assert isinstance(result[0], Campaign)
        assert result[0].id == 1
        assert result[0].name == "Camp1"

    async def test_returns_empty_list_when_no_campaigns(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getCampaigns"), json=[])
        result = await async_client.get_campaigns(complete_json=True)
        assert result == []

    async def test_sends_complete_json_flag_true(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getCampaigns"), json=[])
        await async_client.get_campaigns(complete_json=True)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["complete_json"] == 1

    async def test_sends_complete_json_flag_false_by_default(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getCampaigns"), json=[])
        await async_client.get_campaigns()
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["complete_json"] == 0


class TestGetCampaignSoftBounces:
    async def test_returns_list_of_soft_bounces(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getCampaignSoftBounces"),
            json=[{
                "email": "u@x.com",
                "bounced_at": "2025-01-01T10:00:00",
                "reason": "Mailbox full",
                "status": "4.2.2",
            }],
        )
        result = await async_client.get_campaign_soft_bounces(CAMPAIGN_ID)
        assert len(result) == 1
        assert isinstance(result[0], CampaignSoftBounce)
        assert result[0].email == "u@x.com"
        assert result[0].reason == "Mailbox full"
        assert result[0].status == "4.2.2"

    async def test_returns_empty_list_when_no_bounces(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getCampaignSoftBounces"), json=[])
        result = await async_client.get_campaign_soft_bounces(CAMPAIGN_ID)
        assert result == []

    async def test_sends_campaign_id(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getCampaignSoftBounces"), json=[])
        await async_client.get_campaign_soft_bounces(CAMPAIGN_ID)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["campaign_id"] == CAMPAIGN_ID


class TestGetCampaignTotalInformation:
    async def test_returns_campaign_total_information(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getCampaignTotalInformation"),
            json={
                "total_delivered": 100,
                "soft_bounces": 2,
                "campaign_url": "https://acumbamail.com/c/1",
                "unsubscribes": 1,
                "complaints": 0,
                "unique_clicks": 10,
                "unopened": 80,
                "emails_to_send": 100,
                "opened": 20,
                "hard_bounces": 0,
                "total_clicks": 15,
            },
        )
        result = await async_client.get_campaign_total_information(CAMPAIGN_ID)
        assert isinstance(result, CampaignTotalInformation)
        assert result.total_delivered == 100
        assert result.opened == 20
        assert result.unique_clicks == 10
        assert result.hard_bounces == 0
        assert result.campaign_url == "https://acumbamail.com/c/1"

    async def test_sends_campaign_id(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getCampaignTotalInformation"),
            json={
                "total_delivered": 0,
                "soft_bounces": 0,
                "campaign_url": "",
                "unsubscribes": 0,
                "complaints": 0,
                "unique_clicks": 0,
                "unopened": 0,
                "emails_to_send": 0,
                "opened": 0,
                "hard_bounces": 0,
                "total_clicks": 0,
            },
        )
        await async_client.get_campaign_total_information(CAMPAIGN_ID)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["campaign_id"] == CAMPAIGN_ID


class TestGetStatsByDate:
    async def test_returns_api_response(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getStatsByDate"),
            json={"2025-01-01": {"opens": 5, "clicks": 2}},
        )
        result = await async_client.get_stats_by_date(
            LIST_ID, datetime(2025, 1, 1), datetime(2025, 1, 31)
        )
        assert result["2025-01-01"]["opens"] == 5

    async def test_sends_formatted_dates_and_list_id(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getStatsByDate"), json={})
        await async_client.get_stats_by_date(LIST_ID, datetime(2025, 3, 1), datetime(2025, 3, 31))
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["list_id"] == LIST_ID
        assert body["date_from"] == "2025-03-01"
        assert body["date_to"] == "2025-03-31"


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

class TestGetTemplates:
    async def test_returns_list_of_templates(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getTemplates"),
            json=[{"id": 123, "name": "Tmpl", "content": "<html/>"}],
        )
        result = await async_client.get_templates()
        assert len(result) == 1
        assert isinstance(result[0], Template)
        assert result[0].id == 123
        assert result[0].name == "Tmpl"

    async def test_returns_empty_list_when_no_templates(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getTemplates"), json=[])
        result = await async_client.get_templates()
        assert result == []


class TestCreateTemplate:
    async def test_returns_template_with_id(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("createTemplate"), json=789, status_code=201)
        result = await async_client.create_template(
            template_name="My Template",
            html_content="<p>Hello *|UNSUBSCRIBE_URL|*</p>",
            subject="Hello",
        )
        assert isinstance(result, Template)
        assert result.id == 789
        assert result.name == "My Template"

    async def test_raises_when_content_missing_unsubscribe_url(self, async_client):
        with pytest.raises(AcumbamailValidationError):
            await async_client.create_template(
                template_name="My Template",
                html_content="<p>No unsubscribe link</p>",
                subject="Hello",
            )

    async def test_raises_when_template_name_empty(self, async_client):
        with pytest.raises(AcumbamailValidationError):
            await async_client.create_template("", "<p>*|UNSUBSCRIBE_URL|*</p>", "Subj")

    async def test_raises_when_subject_empty(self, async_client):
        with pytest.raises(AcumbamailValidationError):
            await async_client.create_template("Name", "<p>*|UNSUBSCRIBE_URL|*</p>", "")

    async def test_raises_when_html_content_empty(self, async_client):
        with pytest.raises(AcumbamailValidationError):
            await async_client.create_template("Name", "", "Subj")

    async def test_sends_correct_params(self, async_client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("createTemplate"), json=789, status_code=201)
        await async_client.create_template(
            template_name="My Template",
            html_content="<p>Hello *|UNSUBSCRIBE_URL|*</p>",
            subject="Hello",
            custom_category="transactional",
        )
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["template_name"] == "My Template"
        assert body["subject"] == "Hello"
        assert body["custom_category"] == "transactional"
        assert "*|UNSUBSCRIBE_URL|*" in body["html_content"]


class TestAsyncCreateCampaignValidation:
    async def test_raises_when_name_empty(self, async_client, httpx_mock):
        async with AsyncAcumbamailClient(
            auth_token=TOKEN,
            default_sender_email="sender@test.com",
        ) as client:
            with pytest.raises(AcumbamailValidationError):
                await client.create_campaign(
                    name="", subject="s", content="<p>*|UNSUBSCRIBE_URL|*</p>",
                    list_ids=[123]
                )

    async def test_raises_when_name_whitespace(self, async_client, httpx_mock):
        async with AsyncAcumbamailClient(
            auth_token=TOKEN,
            default_sender_email="sender@test.com",
        ) as client:
            with pytest.raises(AcumbamailValidationError):
                await client.create_campaign(
                    name="   ", subject="s", content="<p>*|UNSUBSCRIBE_URL|*</p>",
                    list_ids=[123]
                )

    async def test_raises_when_subject_empty(self, async_client, httpx_mock):
        async with AsyncAcumbamailClient(
            auth_token=TOKEN,
            default_sender_email="sender@test.com",
        ) as client:
            with pytest.raises(AcumbamailValidationError):
                await client.create_campaign(
                    name="n", subject="", content="<p>*|UNSUBSCRIBE_URL|*</p>",
                    list_ids=[123]
                )

    async def test_raises_when_no_unsubscribe_url(self, async_client, httpx_mock):
        async with AsyncAcumbamailClient(
            auth_token=TOKEN,
            default_sender_email="sender@test.com",
        ) as client:
            with pytest.raises(AcumbamailValidationError):
                await client.create_campaign(
                    name="n", subject="s", content="<p>no url here</p>",
                    list_ids=[123]
                )

    async def test_raises_when_no_list_ids(self, async_client, httpx_mock):
        async with AsyncAcumbamailClient(
            auth_token=TOKEN,
            default_sender_email="sender@test.com",
        ) as client:
            with pytest.raises(AcumbamailValidationError):
                await client.create_campaign(
                    name="n", subject="s", content="<p>*|UNSUBSCRIBE_URL|*</p>",
                    list_ids=[]
                )

    async def test_raises_when_content_empty(self, async_client, httpx_mock):
        async with AsyncAcumbamailClient(
            auth_token=TOKEN,
            default_sender_email="sender@test.com",
        ) as client:
            with pytest.raises(AcumbamailValidationError):
                await client.create_campaign(
                    name="n", subject="s", content="",
                    list_ids=[123]
                )


class TestAsyncSendSingleEmailValidation:
    async def test_raises_when_invalid_email(self, async_client, httpx_mock):
        async with AsyncAcumbamailClient(
            auth_token=TOKEN,
            default_sender_email="sender@test.com",
        ) as client:
            with pytest.raises(AcumbamailValidationError):
                await client.send_single_email(
                    to_email="notanemail", subject="s", content="<p>body</p>"
                )

    async def test_raises_when_subject_empty(self, async_client, httpx_mock):
        async with AsyncAcumbamailClient(
            auth_token=TOKEN,
            default_sender_email="sender@test.com",
        ) as client:
            with pytest.raises(AcumbamailValidationError):
                await client.send_single_email(
                    to_email="x@test.com", subject="", content="<p>body</p>"
                )

    async def test_raises_when_content_empty(self, async_client, httpx_mock):
        async with AsyncAcumbamailClient(
            auth_token=TOKEN,
            default_sender_email="sender@test.com",
        ) as client:
            with pytest.raises(AcumbamailValidationError):
                await client.send_single_email(
                    to_email="x@test.com", subject="s", content=""
                )
