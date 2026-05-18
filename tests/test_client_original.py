"""Tests para los métodos originales (pre-sesión) del cliente síncrono."""
import json
import pytest
from datetime import datetime
from pytest_httpx import HTTPXMock

from acumbamail import AcumbamailClient
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

TOKEN = "test_token"
LIST_ID = 1138335
CAMPAIGN_ID = 999
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
# Lists
# ---------------------------------------------------------------------------

class TestGetLists:
    def test_returns_list_of_mail_lists(self, client, httpx_mock: HTTPXMock):
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
        result = client.get_lists()
        assert len(result) == 1
        assert isinstance(result[0], MailList)
        assert result[0].id == 1138335
        assert result[0].name == "Newsletter"
        assert result[0].subscribers_count == 9

    def test_calls_get_list_stats_for_each_list(self, client, httpx_mock: HTTPXMock):
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
        result = client.get_lists()
        assert len(result) == 2

    def test_returns_empty_list_when_no_lists(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getLists"), json={})
        result = client.get_lists()
        assert result == []

    def test_mail_list_has_bounce_count(self, client, httpx_mock: HTTPXMock):
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
        result = client.get_lists()
        assert result[0].bounced_count == 3
        assert result[0].unsubscribed_count == 2


class TestCreateList:
    def test_returns_mail_list_with_id(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("createList"), json=456, status_code=201)
        result = client.create_list("My Newsletter")
        assert isinstance(result, MailList)
        assert result.id == 456
        assert result.name == "My Newsletter"

    def test_raises_when_no_default_sender_email(self):
        c = AcumbamailClient(auth_token=TOKEN)
        with pytest.raises(AcumbamailValidationError):
            c.create_list("My List")

    def test_raises_when_name_is_empty(self, client):
        with pytest.raises(AcumbamailValidationError):
            client.create_list("")

    def test_raises_when_name_is_whitespace(self, client):
        with pytest.raises(AcumbamailValidationError):
            client.create_list("   ")

    def test_sends_sender_email_from_default(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("createList"), json=456, status_code=201)
        client.create_list("My List")
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["sender_email"] == "sender@test.com"

    def test_sends_name_and_description(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("createList"), json=456, status_code=201)
        client.create_list("My List", description="A description")
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["name"] == "My List"
        assert body["description"] == "A description"

    def test_includes_company_when_set(self, httpx_mock: HTTPXMock):
        c = AcumbamailClient(
            auth_token=TOKEN,
            default_sender_email="x@x.com",
            sender_company="Acme Inc",
        )
        httpx_mock.add_response(url=api_url("createList"), json=1, status_code=201)
        c.create_list("List")
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["company"] == "Acme Inc"


class TestGetSubscribers:
    def test_returns_list_of_subscribers(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getSubscribers"),
            json={"test@test.com": {"status": "active", "id": 5678, "email": "test@test.com"}},
        )
        result = client.get_subscribers(LIST_ID)
        assert len(result) == 1
        assert isinstance(result[0], Subscriber)
        assert result[0].email == "test@test.com"
        assert result[0].list_id == LIST_ID

    def test_returns_empty_list_when_no_subscribers(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getSubscribers"), json={})
        result = client.get_subscribers(LIST_ID)
        assert result == []

    def test_sends_list_id(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getSubscribers"), json={})
        client.get_subscribers(LIST_ID)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["list_id"] == LIST_ID


class TestAddSubscriber:
    def test_returns_subscriber_object(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("addSubscriber"), json=5678, status_code=201)
        result = client.add_subscriber("user@test.com", LIST_ID)
        assert isinstance(result, Subscriber)
        assert result.email == "user@test.com"
        assert result.list_id == LIST_ID

    def test_raises_when_email_invalid(self, client):
        with pytest.raises(AcumbamailValidationError):
            client.add_subscriber("notanemail", LIST_ID)

    def test_raises_when_email_empty(self, client):
        with pytest.raises(AcumbamailValidationError):
            client.add_subscriber("", LIST_ID)

    def test_sends_email_in_merge_fields(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("addSubscriber"), json=5678, status_code=201)
        client.add_subscriber("user@test.com", LIST_ID)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["list_id"] == LIST_ID
        assert body["merge_fields"]["email"] == "user@test.com"

    def test_includes_custom_fields(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("addSubscriber"), json=5678, status_code=201)
        client.add_subscriber("user@test.com", LIST_ID, fields={"name": "John"})
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["merge_fields"]["name"] == "John"

    def test_lowercases_email(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("addSubscriber"), json=5678, status_code=201)
        result = client.add_subscriber("USER@TEST.COM", LIST_ID)
        assert result.email == "user@test.com"


class TestDeleteSubscriber:
    def test_calls_api_with_correct_params(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("deleteSubscriber"),
            json={"email": "test@test.com"},
            status_code=201,
        )
        client.delete_subscriber("test@test.com", LIST_ID)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["list_id"] == LIST_ID
        assert body["email"] == "test@test.com"

    def test_raises_when_email_invalid(self, client):
        with pytest.raises(AcumbamailValidationError):
            client.delete_subscriber("notanemail", LIST_ID)

    def test_raises_when_email_empty(self, client):
        with pytest.raises(AcumbamailValidationError):
            client.delete_subscriber("", LIST_ID)

    def test_returns_none(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("deleteSubscriber"),
            json={"email": "test@test.com"},
            status_code=201,
        )
        result = client.delete_subscriber("test@test.com", LIST_ID)
        assert result is None


class TestGetListStats:
    def test_returns_stats_dict(self, client, httpx_mock: HTTPXMock):
        stats = {
            "total_subscribers": 9,
            "unsubscribed_subscribers": 0,
            "hard_bounced_subscribers": 0,
            "campaigns_sent": 5,
        }
        httpx_mock.add_response(url=api_url("getListStats"), json=stats)
        result = client.get_list_stats(LIST_ID)
        assert result["total_subscribers"] == 9
        assert result["campaigns_sent"] == 5

    def test_sends_list_id(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getListStats"), json={})
        client.get_list_stats(LIST_ID)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["list_id"] == LIST_ID


class TestGetListFields:
    def test_returns_api_response(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getListFields"),
            json=[{"name": "email", "type": "email"}],
        )
        result = client.get_list_fields(LIST_ID)
        assert result == [{"name": "email", "type": "email"}]

    def test_sends_list_id(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getListFields"), json=[])
        client.get_list_fields(LIST_ID)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["list_id"] == LIST_ID


class TestGetListSegments:
    def test_returns_api_response(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getListSegments"),
            json=[{"id": 1, "name": "Segment A"}],
        )
        result = client.get_list_segments(LIST_ID)
        assert result == [{"id": 1, "name": "Segment A"}]

    def test_sends_list_id(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getListSegments"), json=[])
        client.get_list_segments(LIST_ID)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["list_id"] == LIST_ID


class TestGetListSubsStats:
    def test_returns_stats_dict(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getListSubsStats"),
            json={"active": 100, "unsubscribed": 5},
        )
        result = client.get_list_subs_stats(LIST_ID)
        assert result == {"active": 100, "unsubscribed": 5}

    def test_sends_list_id(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getListSubsStats"), json={})
        client.get_list_subs_stats(LIST_ID)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["list_id"] == LIST_ID


class TestGetMergeFields:
    def test_returns_api_response(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getMergeFields"),
            json=[{"field_name": "nombre", "field_type": "text"}],
        )
        result = client.get_merge_fields(LIST_ID)
        assert result == [{"field_name": "nombre", "field_type": "text"}]

    def test_sends_list_id(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getMergeFields"), json=[])
        client.get_merge_fields(LIST_ID)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["list_id"] == LIST_ID


# ---------------------------------------------------------------------------
# Campaigns
# ---------------------------------------------------------------------------

UNSUBSCRIBE_CONTENT = "<p>Hello *|UNSUBSCRIBE_URL|*</p>"


class TestCreateCampaign:
    def test_returns_campaign_with_id(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("createCampaign"), json=99, status_code=201)
        campaign = client.create_campaign(
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

    def test_raises_when_no_from_email(self):
        c = AcumbamailClient(auth_token=TOKEN)
        with pytest.raises(AcumbamailValidationError):
            c.create_campaign("name", "subj", UNSUBSCRIBE_CONTENT, [LIST_ID])

    def test_raises_when_content_missing_unsubscribe_url(self, client):
        with pytest.raises(AcumbamailValidationError):
            client.create_campaign("name", "subj", "<p>No unsubscribe link</p>", [LIST_ID])

    def test_raises_when_name_is_empty(self, client):
        with pytest.raises(AcumbamailValidationError):
            client.create_campaign("", "subj", UNSUBSCRIBE_CONTENT, [LIST_ID])

    def test_raises_when_subject_is_empty(self, client):
        with pytest.raises(AcumbamailValidationError):
            client.create_campaign("name", "", UNSUBSCRIBE_CONTENT, [LIST_ID])

    def test_raises_when_list_ids_is_empty(self, client):
        with pytest.raises(AcumbamailValidationError):
            client.create_campaign("name", "subj", UNSUBSCRIBE_CONTENT, [])

    def test_uses_default_sender_email(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("createCampaign"), json=1, status_code=201)
        client.create_campaign("name", "subj", UNSUBSCRIBE_CONTENT, [LIST_ID])
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["from_email"] == "sender@test.com"

    def test_overrides_from_email_when_provided(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("createCampaign"), json=1, status_code=201)
        client.create_campaign(
            "name", "subj", UNSUBSCRIBE_CONTENT, [LIST_ID],
            from_email="other@test.com",
        )
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["from_email"] == "other@test.com"

    def test_includes_scheduled_at_when_provided(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("createCampaign"), json=1, status_code=201)
        scheduled = datetime(2026, 3, 15, 9, 0)
        client.create_campaign(
            "name", "subj", UNSUBSCRIBE_CONTENT, [LIST_ID],
            scheduled_at=scheduled,
        )
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["date_send"] == "2026-03-15 09:00"

    def test_does_not_include_date_send_when_not_scheduled(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("createCampaign"), json=1, status_code=201)
        client.create_campaign("name", "subj", UNSUBSCRIBE_CONTENT, [LIST_ID])
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert "date_send" not in body


class TestSendSingleEmail:
    def test_returns_email_id(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("sendOne"), json=5678)
        result = client.send_single_email(
            to_email="to@test.com",
            subject="Hello",
            content="<p>Body</p>",
        )
        assert result == 5678

    def test_raises_when_no_from_email(self):
        c = AcumbamailClient(auth_token=TOKEN)
        with pytest.raises(AcumbamailValidationError):
            c.send_single_email("to@test.com", "subj", "body")

    def test_raises_when_to_email_invalid(self, client):
        with pytest.raises(AcumbamailValidationError):
            client.send_single_email("notanemail", "subj", "body")

    def test_raises_when_subject_empty(self, client):
        with pytest.raises(AcumbamailValidationError):
            client.send_single_email("to@test.com", "", "body")

    def test_raises_when_content_empty(self, client):
        with pytest.raises(AcumbamailValidationError):
            client.send_single_email("to@test.com", "subj", "")

    def test_sends_correct_params(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("sendOne"), json=1)
        client.send_single_email(
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
    def test_returns_api_response(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getCampaignBasicInformation"),
            json={"name": "Camp1", "subject": "Subj"},
        )
        result = client.get_campaign_basic_information(CAMPAIGN_ID)
        assert result["name"] == "Camp1"
        assert result["subject"] == "Subj"

    def test_sends_campaign_id(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getCampaignBasicInformation"), json={})
        client.get_campaign_basic_information(CAMPAIGN_ID)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["campaign_id"] == CAMPAIGN_ID


class TestGetCampaignClicks:
    def test_returns_list_of_campaign_clicks(self, client, httpx_mock: HTTPXMock):
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
        result = client.get_campaign_clicks(CAMPAIGN_ID)
        assert len(result) == 1
        assert isinstance(result[0], CampaignClick)
        assert result[0].url == "https://x.com"
        assert result[0].clicks == 10
        assert result[0].unique_clicks == 8

    def test_returns_empty_list_when_no_clicks(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getCampaignClicks"), json=[])
        result = client.get_campaign_clicks(CAMPAIGN_ID)
        assert result == []

    def test_sends_campaign_id(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getCampaignClicks"), json=[])
        client.get_campaign_clicks(CAMPAIGN_ID)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["campaign_id"] == CAMPAIGN_ID


class TestGetCampaignInformationByISP:
    def test_returns_dict(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getCampaignInformationByISP"),
            json={"Gmail": {"sent": 50, "opened": 20}},
        )
        result = client.get_campaign_information_by_isp(CAMPAIGN_ID)
        assert result["Gmail"]["sent"] == 50

    def test_sends_campaign_id(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getCampaignInformationByISP"), json={})
        client.get_campaign_information_by_isp(CAMPAIGN_ID)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["campaign_id"] == CAMPAIGN_ID


class TestGetCampaignLinks:
    def test_returns_list_of_links(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getCampaignLinks"),
            json=["https://a.com", "https://b.com"],
        )
        result = client.get_campaign_links(CAMPAIGN_ID)
        assert result == ["https://a.com", "https://b.com"]

    def test_sends_campaign_id(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getCampaignLinks"), json=[])
        client.get_campaign_links(CAMPAIGN_ID)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["campaign_id"] == CAMPAIGN_ID


class TestGetCampaignOpeners:
    def test_returns_list_of_campaign_openers(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getCampaignOpeners"),
            json=[{"email": "u@x.com", "opened_at": "2025-01-01T10:00:00"}],
        )
        result = client.get_campaign_openers(CAMPAIGN_ID)
        assert len(result) == 1
        assert isinstance(result[0], CampaignOpener)
        assert result[0].email == "u@x.com"

    def test_returns_empty_list_when_no_openers(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getCampaignOpeners"), json=[])
        result = client.get_campaign_openers(CAMPAIGN_ID)
        assert result == []

    def test_sends_campaign_id(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getCampaignOpeners"), json=[])
        client.get_campaign_openers(CAMPAIGN_ID)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["campaign_id"] == CAMPAIGN_ID


class TestGetCampaignOpenersByBrowser:
    def test_returns_dict(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getCampaignOpenersByBrowser"),
            json={"Chrome": 50, "Firefox": 10},
        )
        result = client.get_campaign_openers_by_browser(CAMPAIGN_ID)
        assert result == {"Chrome": 50, "Firefox": 10}

    def test_sends_campaign_id(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getCampaignOpenersByBrowser"), json={})
        client.get_campaign_openers_by_browser(CAMPAIGN_ID)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["campaign_id"] == CAMPAIGN_ID


class TestGetCampaignOpenersByOs:
    def test_returns_dict(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getCampaignOpenersByOs"),
            json={"macOS": 30, "Windows": 20},
        )
        result = client.get_campaign_openers_by_os(CAMPAIGN_ID)
        assert result == {"macOS": 30, "Windows": 20}

    def test_sends_campaign_id(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getCampaignOpenersByOs"), json={})
        client.get_campaign_openers_by_os(CAMPAIGN_ID)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["campaign_id"] == CAMPAIGN_ID


class TestGetCampaigns:
    def test_returns_list_of_campaigns(self, client, httpx_mock: HTTPXMock):
        # Real API returns [{str_id: campaign_name}, ...] — one key per item
        httpx_mock.add_response(
            url=api_url("getCampaigns"),
            json=[{"1": "Camp1"}],
        )
        result = client.get_campaigns(complete_json=True)
        assert len(result) == 1
        assert isinstance(result[0], Campaign)
        assert result[0].id == 1
        assert result[0].name == "Camp1"

    def test_returns_empty_list_when_no_campaigns(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getCampaigns"), json=[])
        result = client.get_campaigns(complete_json=True)
        assert result == []

    def test_sends_complete_json_flag_true(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getCampaigns"), json=[])
        client.get_campaigns(complete_json=True)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["complete_json"] == 1

    def test_sends_complete_json_flag_false_by_default(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getCampaigns"), json=[])
        client.get_campaigns()
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["complete_json"] == 0


class TestGetCampaignSoftBounces:
    def test_returns_list_of_soft_bounces(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getCampaignSoftBounces"),
            json=[{
                "email": "u@x.com",
                "bounced_at": "2025-01-01T10:00:00",
                "reason": "Mailbox full",
                "status": "4.2.2",
            }],
        )
        result = client.get_campaign_soft_bounces(CAMPAIGN_ID)
        assert len(result) == 1
        assert isinstance(result[0], CampaignSoftBounce)
        assert result[0].email == "u@x.com"
        assert result[0].reason == "Mailbox full"
        assert result[0].status == "4.2.2"

    def test_returns_empty_list_when_no_bounces(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getCampaignSoftBounces"), json=[])
        result = client.get_campaign_soft_bounces(CAMPAIGN_ID)
        assert result == []

    def test_sends_campaign_id(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getCampaignSoftBounces"), json=[])
        client.get_campaign_soft_bounces(CAMPAIGN_ID)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["campaign_id"] == CAMPAIGN_ID


class TestGetCampaignTotalInformation:
    def test_returns_campaign_total_information(self, client, httpx_mock: HTTPXMock):
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
        result = client.get_campaign_total_information(CAMPAIGN_ID)
        assert isinstance(result, CampaignTotalInformation)
        assert result.total_delivered == 100
        assert result.opened == 20
        assert result.unique_clicks == 10
        assert result.hard_bounces == 0
        assert result.campaign_url == "https://acumbamail.com/c/1"

    def test_sends_campaign_id(self, client, httpx_mock: HTTPXMock):
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
        client.get_campaign_total_information(CAMPAIGN_ID)
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["campaign_id"] == CAMPAIGN_ID


class TestGetStatsByDate:
    def test_returns_api_response(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getStatsByDate"),
            json={"2025-01-01": {"opens": 5, "clicks": 2}},
        )
        result = client.get_stats_by_date(
            LIST_ID, datetime(2025, 1, 1), datetime(2025, 1, 31)
        )
        assert result["2025-01-01"]["opens"] == 5

    def test_sends_formatted_dates_and_list_id(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getStatsByDate"), json={})
        client.get_stats_by_date(LIST_ID, datetime(2025, 3, 1), datetime(2025, 3, 31))
        body = json.loads(httpx_mock.get_requests()[0].content)
        assert body["list_id"] == LIST_ID
        assert body["date_from"] == "2025-03-01"
        assert body["date_to"] == "2025-03-31"


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

class TestGetTemplates:
    def test_returns_list_of_templates(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=api_url("getTemplates"),
            json=[{"id": 123, "name": "Tmpl", "content": "<html/>"}],
        )
        result = client.get_templates()
        assert len(result) == 1
        assert isinstance(result[0], Template)
        assert result[0].id == 123
        assert result[0].name == "Tmpl"

    def test_returns_empty_list_when_no_templates(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("getTemplates"), json=[])
        result = client.get_templates()
        assert result == []


class TestCreateTemplate:
    def test_returns_template_with_id(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("createTemplate"), json=789, status_code=201)
        result = client.create_template(
            template_name="My Template",
            html_content="<p>Hello *|UNSUBSCRIBE_URL|*</p>",
            subject="Hello",
        )
        assert isinstance(result, Template)
        assert result.id == 789
        assert result.name == "My Template"

    def test_raises_when_content_missing_unsubscribe_url(self, client):
        with pytest.raises(AcumbamailValidationError):
            client.create_template(
                template_name="My Template",
                html_content="<p>No unsubscribe link</p>",
                subject="Hello",
            )

    def test_raises_when_template_name_empty(self, client):
        with pytest.raises(AcumbamailValidationError):
            client.create_template("", "<p>*|UNSUBSCRIBE_URL|*</p>", "Subj")

    def test_raises_when_subject_empty(self, client):
        with pytest.raises(AcumbamailValidationError):
            client.create_template("Name", "<p>*|UNSUBSCRIBE_URL|*</p>", "")

    def test_raises_when_html_content_empty(self, client):
        with pytest.raises(AcumbamailValidationError):
            client.create_template("Name", "", "Subj")

    def test_sends_correct_params(self, client, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=api_url("createTemplate"), json=789, status_code=201)
        client.create_template(
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
