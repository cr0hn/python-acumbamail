"""Tests de cobertura: spec vs implementación SDK."""
import re
import yaml
import pytest
from pathlib import Path

SPEC_PATH = Path(__file__).parent.parent / "acumbamail-openapi.yaml"
CLIENT_PATH = Path(__file__).parent.parent / "acumbamail" / "client.py"


@pytest.fixture(scope="module")
def spec() -> dict:
    return yaml.safe_load(SPEC_PATH.read_text())


@pytest.fixture(scope="module")
def spec_endpoints(spec) -> set:
    """Endpoints en el spec (sin slashes)."""
    return {p.strip("/") for p in spec["paths"].keys()}


@pytest.fixture(scope="module")
def sdk_endpoints() -> set:
    """Endpoints llamados en client.py vía _call_api('endpoint', ...)."""
    source = CLIENT_PATH.read_text()
    return set(re.findall(r'_call_api\(\s*["\']([A-Za-z]+)["\']', source))


class TestCoverage:
    def test_all_sdk_endpoints_in_spec(self, sdk_endpoints, spec_endpoints):
        """Cada endpoint que usa el SDK está documentado en el spec."""
        missing = sdk_endpoints - spec_endpoints
        assert not missing, f"Endpoints del SDK sin documentar en spec: {missing}"

    def test_spec_has_no_unknown_endpoints(self, sdk_endpoints, spec_endpoints):
        """No hay endpoints en el spec que el SDK no use."""
        # SMTP batch y transaccional: documentados, requieren plan activo
        # getTemplatesByName: documentado en API oficial pero retorna 404 server-side
        known_extra = {"send", "sendCertifiedEmail", "sendOne", "getEmailStatus", "getTemplatesByName"}
        unknown = spec_endpoints - sdk_endpoints - known_extra
        assert not unknown, f"Endpoints en spec sin usar en SDK: {unknown}"

    def test_get_templates_by_name_is_in_spec(self, spec_endpoints):
        """getTemplatesByName está en el spec (documentado pero no implementado en servidor)."""
        assert "getTemplatesByName" in spec_endpoints

    def test_get_templates_by_name_is_marked_not_implemented(self, spec):
        """getTemplatesByName tiene la extension x-status: documented-not-implemented."""
        op = spec["paths"]["/getTemplatesByName/"]["post"]
        assert op.get("x-status") == "documented-not-implemented"
        # Y su descripción advierte del problema
        assert "404" in op.get("description", "") or "not implemented" in op.get("description", "").lower()

    def test_spec_covers_subscriber_endpoints(self, spec_endpoints):
        expected = {
            "getLists", "createList", "deleteList", "getListStats",
            "getSubscribers", "addSubscriber", "deleteSubscriber",
            "batchAddSubscribers", "unsubscribeSubscriber",
            "getSubscriberDetails", "searchSubscriber", "getInactiveSubscribers",
        }
        missing = expected - spec_endpoints
        assert not missing, f"Faltan endpoints de suscriptores: {missing}"

    def test_spec_covers_campaign_endpoints(self, spec_endpoints):
        expected = {
            "createCampaign", "getCampaigns", "getCampaignTotalInformation",
            "getCampaignClicks", "getCampaignOpeners", "getCampaignSoftBounces",
            "getCampaignOpenersByBrowser", "getCampaignOpenersByOs",
            "getCampaignOpenersByCountries",
        }
        missing = expected - spec_endpoints
        assert not missing, f"Faltan endpoints de campañas: {missing}"

    def test_spec_covers_webhook_endpoints(self, spec_endpoints):
        expected = {
            "getSMTPWebhook", "configSMTPWebhook",
            "getListWebhook", "configListWebhook",
        }
        missing = expected - spec_endpoints
        assert not missing, f"Faltan endpoints de webhooks: {missing}"

    def test_broken_endpoints_are_documented(self, spec) -> None:
        """batchDeleteSubscribers debe documentar que devuelve 500."""
        path = spec["paths"].get("/batchDeleteSubscribers/", {})
        op = path.get("post", {})
        # Debe tener 500 en responses O mencionarlo en la description
        has_500 = "500" in op.get("responses", {})
        has_note = "500" in (op.get("description", "") + op.get("summary", ""))
        assert has_500 or has_note, "batchDeleteSubscribers no documenta el bug del 500"

    def test_smtp_endpoints_document_requirement(self, spec):
        """Endpoints SMTP deben documentar que requieren plan activo."""
        smtp_endpoints = ["/sendOne/", "/send/", "/sendCertifiedEmail/", "/getEmailStatus/"]
        for path in smtp_endpoints:
            op = spec["paths"].get(path, {}).get("post", {})
            desc = (op.get("description", "") + op.get("summary", "")).lower()
            assert any(w in desc for w in ["smtp", "active", "activ", "plan", "401"]), \
                f"{path} no documenta el requisito de SMTP activo"
