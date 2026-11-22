"""The calls Pulse (FastAPI service) uses, sync and async, with HTTP mocked, plus packaging guards."""
import json
import subprocess
import sys

from acumbamail import AcumbamailClient, AsyncAcumbamailClient
from tests.conftest import HTTPXMock, LIST_ID, TOKEN, api_url

HTML = "<p>Hi *|UNSUBSCRIBE_URL|*</p>"


def _client() -> AcumbamailClient:
    return AcumbamailClient(auth_token=TOKEN, default_sender_name="Dani", default_sender_email="d@x.com")


def _aclient() -> AsyncAcumbamailClient:
    return AsyncAcumbamailClient(auth_token=TOKEN, default_sender_name="Dani", default_sender_email="d@x.com")


def _body(httpx_mock: HTTPXMock) -> dict[str, object]:
    body: dict[str, object] = json.loads(httpx_mock.get_requests()[-1].content)
    return body


def test_add_subscriber_with_merge_fields(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=api_url("addSubscriber"), json=1)
    sub = _client().add_subscriber("A@x.com", LIST_ID, {"nombre": "Ana", "ref_url": "https://r"}, update_subscriber=True)
    body = _body(httpx_mock)
    assert sub.email == "a@x.com"
    assert body["merge_fields"] == {"email": "a@x.com", "nombre": "Ana", "ref_url": "https://r"}
    assert body["update_subscriber"] == 1 and body["double_optin"] == 0


def test_unsubscribe_and_delete(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=api_url("unsubscribeSubscriber"), json={})
    httpx_mock.add_response(url=api_url("deleteSubscriber"), json={"email": "a@x.com"})
    client = _client()
    client.unsubscribe_subscriber(LIST_ID, "a@x.com")
    client.delete_subscriber("a@x.com", LIST_ID)
    urls = [str(r.url) for r in httpx_mock.get_requests()]
    assert urls == [api_url("unsubscribeSubscriber"), api_url("deleteSubscriber")]


def test_create_campaign_and_send(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=api_url("createCampaign"), json={"id": 77})
    campaign = _client().create_campaign("n", "subj", HTML, [LIST_ID])
    body = _body(httpx_mock)
    assert campaign.id == 77
    assert body["lists"] == [LIST_ID] and body["content"] == HTML and "date_send" not in body


def test_campaign_stats(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=api_url("getCampaignTotalInformation"),
        json={"total_delivered": 10, "opened": 4, "unique_clicks": 2, "total_clicks": 3},
    )
    info = _client().get_campaign_total_information(77)
    assert (info.total_delivered, info.opened, info.total_clicks) == (10, 4, 3)


def test_send_transactional(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=api_url("sendOne"), json=123)
    assert _client().send_single_email("a@x.com", "s", HTML, category="welcome") == 123
    assert _body(httpx_mock)["to_email"] == "a@x.com"


async def test_async_surface(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=api_url("addSubscriber"), json=1)
    httpx_mock.add_response(url=api_url("unsubscribeSubscriber"), json={})
    httpx_mock.add_response(url=api_url("createCampaign"), json={"id": 5})
    httpx_mock.add_response(url=api_url("getCampaignTotalInformation"), json={"total_delivered": 1, "opened": 1})
    httpx_mock.add_response(url=api_url("sendOne"), json=9)
    async with _aclient() as client:
        await client.add_subscriber("a@x.com", LIST_ID, {"nombre": "Ana"})
        await client.unsubscribe_subscriber(LIST_ID, "a@x.com")
        assert (await client.create_campaign("n", "s", HTML, [LIST_ID])).id == 5
        assert (await client.get_campaign_total_information(5)).opened == 1
        assert await client.send_single_email("a@x.com", "s", HTML) == 9


def test_import_does_not_load_browser_extras() -> None:
    code = "import sys, acumbamail; sys.exit(any(m.split('.')[0] in ('playwright', 'undetected_chromedriver', 'selenium') for m in sys.modules))"
    assert subprocess.run([sys.executable, "-I", "-c", code]).returncode == 0
