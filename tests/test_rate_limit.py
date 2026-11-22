"""Tests para BUG 6: el backoff de rate limit no debe morir por timeout.

El bug real: el backoff anuncia "Waiting N seconds" pero el read timeout del
cliente HTTP era mas corto que esa espera, asi que el reintento moria con
"The read operation timed out". El fix respeta `Retry-After` si viene, y
sube el timeout de la peticion reintentada por encima de la espera anunciada.

Se usan clientes httpx2 falsos (sin red real) para poder verificar tanto el
tiempo de espera usado como el timeout con el que se construye/llama al
cliente HTTP en cada intento — pytest-httpx2 no expone ese dato.
"""
import httpx2
import pytest

from acumbamail import AcumbamailClient, AsyncAcumbamailClient

TOKEN = "test_token"


class _FakeResponse:
    def __init__(self, status_code, json_data=None, headers=None):
        self.status_code = status_code
        self._json_data = json_data if json_data is not None else {}
        self.headers = headers or {}
        self.text = ""

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx2.HTTPStatusError("error", request=None, response=self)


class _FakeSyncClient:
    """Sustituto de httpx2.Client: registra el timeout con el que se
    construyo y sirve una secuencia de respuestas guionizada."""
    responses = []
    timeouts_used = []

    def __init__(self, timeout=None):
        _FakeSyncClient.timeouts_used.append(timeout)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def post(self, url, json=None):
        return _FakeSyncClient.responses.pop(0)


class _FakeAsyncClient:
    """Sustituto de httpx2.AsyncClient: registra el timeout por-peticion."""
    responses = []
    timeouts_used = []

    def __init__(self, timeout=None):
        pass

    async def post(self, url, json=None, timeout=None):
        _FakeAsyncClient.timeouts_used.append(timeout)
        return _FakeAsyncClient.responses.pop(0)

    async def aclose(self):
        pass


@pytest.fixture(autouse=True)
def _reset_fakes():
    _FakeSyncClient.responses = []
    _FakeSyncClient.timeouts_used = []
    _FakeAsyncClient.responses = []
    _FakeAsyncClient.timeouts_used = []
    yield


class TestSyncRateLimitBackoffTimeout:
    def test_retry_after_header_is_respected_and_timeout_raised_above_wait(self, monkeypatch):
        # Timeout base deliberadamente corto (como el default de httpx2 antes
        # del fix), mas corto que la espera real que anuncia el 429.
        client = AcumbamailClient(auth_token=TOKEN, timeout=5.0)

        monkeypatch.setattr("acumbamail.client.httpx2.Client", _FakeSyncClient)
        sleeps = []
        monkeypatch.setattr("acumbamail.client.time.sleep", lambda s: sleeps.append(s))

        _FakeSyncClient.responses = [
            _FakeResponse(429, headers={"Retry-After": "40"}),
            _FakeResponse(200, json_data={"id": 1}),
        ]

        result = client._call_api("getLists")

        assert result == {"id": 1}
        # Respeta Retry-After (40s), no el schedule por defecto (10*retries=10s).
        assert sleeps == [40.0]
        # La primera peticion uso el timeout base; la del reintento se subio
        # por encima de la espera anunciada (40s) — nunca puede morir con un
        # read timeout mas corto que el backoff (BUG 6).
        assert _FakeSyncClient.timeouts_used[0] == 5.0
        assert _FakeSyncClient.timeouts_used[1] > 40.0

    def test_falls_back_to_default_schedule_without_retry_after_header(self, monkeypatch):
        client = AcumbamailClient(auth_token=TOKEN, timeout=5.0)
        monkeypatch.setattr("acumbamail.client.httpx2.Client", _FakeSyncClient)
        sleeps = []
        monkeypatch.setattr("acumbamail.client.time.sleep", lambda s: sleeps.append(s))

        _FakeSyncClient.responses = [
            _FakeResponse(429, headers={}),
            _FakeResponse(200, json_data={"id": 1}),
        ]

        client._call_api("getLists")

        assert sleeps == [10]  # 10 * retries(1), el schedule original


class TestAsyncRateLimitBackoffTimeout:
    async def test_retry_after_header_is_respected_and_timeout_raised_above_wait(self, monkeypatch):
        client = AsyncAcumbamailClient(auth_token=TOKEN, timeout=5.0)
        monkeypatch.setattr("acumbamail.aclient.httpx2.AsyncClient", _FakeAsyncClient)
        await client._ensure_client()

        sleeps = []

        async def fake_sleep(s):
            sleeps.append(s)

        monkeypatch.setattr("acumbamail.aclient.asyncio.sleep", fake_sleep)

        _FakeAsyncClient.responses = [
            _FakeResponse(429, headers={"Retry-After": "40"}),
            _FakeResponse(200, json_data={"id": 1}),
        ]

        result = await client._call_api("getLists")

        assert result == {"id": 1}
        assert sleeps == [40.0]
        assert _FakeAsyncClient.timeouts_used[0] == 5.0
        assert _FakeAsyncClient.timeouts_used[1] > 40.0
