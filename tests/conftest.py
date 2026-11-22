import re
from collections.abc import Callable
from typing import Any

import httpx2
import pytest

BASE_URL = "https://acumbamail.com/api/1"
TOKEN = "test_token_123"
LIST_ID = 1138335


class HTTPXMock:
    """Minimal pytest-httpx-style mock (add_response / get_requests) over httpx2.MockTransport.

    Like pytest-httpx: responses registered for the same matcher are served in order and the
    last one is reused; a request nobody registered raises a timeout.
    """

    def __init__(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._entries: list[tuple[Callable[[httpx2.Request], bool], httpx2.Response]] = []
        self._served: list[int] = []
        self._requests: list[httpx2.Request] = []
        transport = httpx2.MockTransport(self._handle)
        for cls in (httpx2.Client, httpx2.AsyncClient):
            original = cls.__init__

            def patched(self_: Any, *args: Any, _orig: Any = original, **kwargs: Any) -> None:
                kwargs.setdefault("transport", transport)
                _orig(self_, *args, **kwargs)

            monkeypatch.setattr(cls, "__init__", patched)

    def add_response(
        self,
        url: str | re.Pattern[str] | None = None,
        method: str | None = None,
        status_code: int = 200,
        **kwargs: Any,
    ) -> None:
        def match(request: httpx2.Request) -> bool:
            if method is not None and request.method != method:
                return False
            if url is None:
                return True
            if isinstance(url, re.Pattern):
                return url.match(str(request.url)) is not None
            return str(request.url) == url

        self._entries.append((match, httpx2.Response(status_code, **kwargs)))

    def get_requests(self) -> list[httpx2.Request]:
        return list(self._requests)

    def _handle(self, request: httpx2.Request) -> httpx2.Response:
        self._requests.append(request)
        matching = [i for i, (m, _) in enumerate(self._entries) if m(request)]
        if not matching:
            raise httpx2.TimeoutException(
                f"No response registered for {request.method} {request.url}", request=request
            )
        fresh = [i for i in matching if i not in self._served]
        index = fresh[0] if fresh else matching[-1]
        self._served.append(index)
        _, response = self._entries[index]
        return httpx2.Response(response.status_code, headers=response.headers, content=response.content)


@pytest.fixture
def httpx_mock(monkeypatch: pytest.MonkeyPatch) -> HTTPXMock:
    return HTTPXMock(monkeypatch)


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
