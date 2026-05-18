import pytest
from pytest_httpx import HTTPXMock
from acumbamail.automation_client import AutomationClient

BASE = "https://acumbamail.com"
LOGIN_HTML = '<form><input name="csrfmiddlewaretoken" value="csrf_token_123"></form>'


@pytest.fixture
def client():
    return AutomationClient("user@test.com", "password123")


def mock_login(httpx_mock: HTTPXMock):
    httpx_mock.add_response(method="GET", url=f"{BASE}/login/", text=LOGIN_HTML, status_code=200)
    httpx_mock.add_response(method="POST", url=f"{BASE}/login/", text="<html>ok</html>", status_code=200)


class TestLogin:
    def test_login_extracts_and_stores_csrf(self, client, httpx_mock: HTTPXMock):
        mock_login(httpx_mock)
        client.login()
        assert client._csrf_token == "csrf_token_123"

    def test_login_sends_credentials_in_post(self, client, httpx_mock: HTTPXMock):
        mock_login(httpx_mock)
        client.login()
        requests = httpx_mock.get_requests()
        post_req = requests[1]
        assert post_req.method == "POST"
        body = post_req.content.decode()
        assert "user%40test.com" in body or "user@test.com" in body
        assert "password123" in body

    def test_extract_csrf_from_html(self, client):
        html = '<input name="csrfmiddlewaretoken" value="abc123">'
        assert client._extract_csrf(html) == "abc123"

    def test_extract_csrf_raises_if_missing(self, client):
        with pytest.raises(ValueError, match="CSRF token not found"):
            client._extract_csrf("<html>no token here</html>")
