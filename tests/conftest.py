import pytest
import httpx
from pytest_httpx import HTTPXMock

BASE_URL = "https://acumbamail.com/api/1"
TOKEN = "test_token_123"
LIST_ID = 1138335


@pytest.fixture
def sync_client():
    from acumbamail import AcumbamailClient
    return AcumbamailClient(
        auth_token=TOKEN,
        default_sender_name="Test Sender",
        default_sender_email="sender@test.com",
    )


@pytest.fixture
def async_client():
    from acumbamail import AsyncAcumbamailClient
    return AsyncAcumbamailClient(
        auth_token=TOKEN,
        default_sender_name="Test Sender",
        default_sender_email="sender@test.com",
    )


def api_url(endpoint: str) -> str:
    return f"{BASE_URL}/{endpoint}/"
