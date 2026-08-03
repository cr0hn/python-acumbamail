"""Tests para acumbamail.utils — normalización de IDs en respuestas de la API."""
import pytest

from acumbamail.utils import manage_api_response_id


class TestManageApiResponseId:
    def test_bare_string(self):
        assert manage_api_response_id("12345") == 12345

    def test_bare_int(self):
        assert manage_api_response_id(67890) == 67890

    def test_id_key(self):
        assert manage_api_response_id({"id": "54321"}) == 54321

    def test_list_id_key_real_createlist_response(self):
        """BUG 1: createList devuelve {"list_id": N}, no {"id": N}."""
        assert manage_api_response_id({"list_id": 456}) == 456

    def test_subscriber_id_key(self):
        assert manage_api_response_id({"subscriber_id": 789}) == 789

    def test_campaign_id_key(self):
        assert manage_api_response_id({"campaign_id": 111}) == 111

    def test_any_key_ending_in_id(self):
        assert manage_api_response_id({"template_id": "222"}) == 222

    def test_legacy_single_entry_dict_key_is_id(self):
        """Forma legacy: la clave ES el id, y el valor no es casteable a int."""
        assert manage_api_response_id({"98765": "some list name"}) == 98765

    def test_invalid_type_raises_value_error(self):
        with pytest.raises(ValueError, match="Invalid response type"):
            manage_api_response_id(["not", "valid"])

    def test_unrecognized_dict_shape_raises_clear_error_not_raw_valueerror(self):
        """No debe filtrar un ValueError crudo de int(); debe decir qué forma llegó."""
        with pytest.raises(ValueError) as exc_info:
            manage_api_response_id({"foo": "bar", "baz": "qux"})
        message = str(exc_info.value)
        assert "id" in message
        assert "foo" in message or "{'foo'" in message or repr({"foo": "bar", "baz": "qux"}) in message
