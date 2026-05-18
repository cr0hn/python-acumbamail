"""Tests de validación estructural del OpenAPI spec."""
import yaml
import pytest
from pathlib import Path
from openapi_spec_validator import validate

SPEC_PATH = Path(__file__).parent.parent / "acumbamail-openapi.yaml"


@pytest.fixture(scope="module")
def spec() -> dict:
    return yaml.safe_load(SPEC_PATH.read_text())


class TestSpecStructure:
    def test_spec_is_valid_openapi_303(self, spec):
        """El spec pasa la validación oficial de OpenAPI 3.0.3."""
        validate(spec)  # lanza excepción si falla

    def test_spec_version_is_303(self, spec):
        assert spec["openapi"] == "3.0.3"

    def test_info_has_title_and_version(self, spec):
        assert spec["info"]["title"] == "Acumbamail API"
        assert spec["info"]["version"]

    def test_server_url_is_correct(self, spec):
        servers = spec["servers"]
        assert any("acumbamail.com/api/1" in s["url"] for s in servers)

    def test_all_paths_use_post(self, spec):
        for path, item in spec["paths"].items():
            methods = set(item.keys())
            assert "post" in methods, f"{path} no tiene método POST"
            extra = methods - {"post"}
            assert not extra, f"{path} tiene métodos inesperados: {extra}"

    def test_all_operations_have_summary(self, spec):
        for path, item in spec["paths"].items():
            op = item.get("post", {})
            assert op.get("summary"), f"{path} no tiene summary"

    def test_all_operations_have_tags(self, spec):
        for path, item in spec["paths"].items():
            op = item.get("post", {})
            assert op.get("tags"), f"{path} no tiene tags"

    def test_all_operations_have_request_body(self, spec):
        for path, item in spec["paths"].items():
            op = item.get("post", {})
            assert op.get("requestBody"), f"{path} no tiene requestBody"

    def test_all_operations_have_at_least_one_response(self, spec):
        for path, item in spec["paths"].items():
            op = item.get("post", {})
            assert op.get("responses"), f"{path} no tiene responses"

    def test_all_operations_have_rate_limit_extension(self, spec):
        for path, item in spec["paths"].items():
            op = item.get("post", {})
            assert "x-rate-limit" in op, f"{path} no tiene x-rate-limit"

    def test_expected_tags_defined(self, spec):
        defined_tags = {t["name"] for t in spec.get("tags", [])}
        expected = {"Lists", "Subscribers", "Campaigns", "Templates", "SMTP", "Webhooks"}
        assert expected == defined_tags

    def test_auth_fields_schema_exists(self, spec):
        schemas = spec["components"]["schemas"]
        assert "AuthFields" in schemas
        auth = schemas["AuthFields"]
        assert "auth_token" in auth["properties"]
        assert "auth_token" in auth["required"]

    def test_error_response_schema_exists(self, spec):
        schemas = spec["components"]["schemas"]
        assert "ErrorResponse" in schemas

    def test_all_schema_refs_resolve(self, spec):
        """Todos los $ref a schemas internos resuelven correctamente."""
        import json
        spec_str = json.dumps(spec)
        schemas = set(spec["components"]["schemas"].keys())

        import re
        refs = re.findall(r'#/components/schemas/([A-Za-z0-9_]+)', spec_str)
        unresolved = set(refs) - schemas
        assert not unresolved, f"$ref no resueltos: {unresolved}"

    def test_all_endpoints_count(self, spec):
        assert len(spec["paths"]) == 47

    def test_all_schemas_count(self, spec):
        assert len(spec["components"]["schemas"]) == 30
