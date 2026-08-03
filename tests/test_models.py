"""Tests para los nuevos modelos del SDK."""
from datetime import datetime

from acumbamail.models import (
    SubscriberDetails,
    InactiveSubscriber,
    InactiveReason,
    SMTPWebhook,
    ListWebhook,
    BatchSubscriberResult,
)


class TestSubscriberDetails:
    def test_from_api_with_all_fields(self):
        data = {
            "id": 5125884584,
            "email": "cr0hn@cr0hn.com",
            "status": "active",
            "create_date": "2025/06/30 07:32:30",
            "list_id": 1138335,
            "custom_field": "custom_value",
        }
        sub = SubscriberDetails.from_api(data)
        assert sub.id == 5125884584
        assert sub.email == "cr0hn@cr0hn.com"
        assert sub.status == "active"
        assert sub.create_date == datetime(2025, 6, 30, 7, 32, 30)
        assert sub.list_id == 1138335
        assert sub.fields == {"custom_field": "custom_value"}

    def test_from_api_without_optional_fields(self):
        data = {"id": 123, "email": "test@test.com", "status": "active"}
        sub = SubscriberDetails.from_api(data)
        assert sub.id == 123
        assert sub.create_date is None
        assert sub.list_id is None
        assert sub.fields is None

    def test_from_api_strips_known_keys_from_fields(self):
        data = {
            "id": 1,
            "email": "a@b.com",
            "status": "active",
            "create_date": "2025/01/01 00:00:00",
            "list_id": 999,
            "extra": "value",
        }
        sub = SubscriberDetails.from_api(data)
        assert "id" not in sub.fields
        assert "email" not in sub.fields
        assert "status" not in sub.fields
        assert "create_date" not in sub.fields
        assert "list_id" not in sub.fields
        assert sub.fields == {"extra": "value"}

    def test_from_api_no_extra_fields_returns_none(self):
        data = {"id": 1, "email": "a@b.com", "status": "active"}
        sub = SubscriberDetails.from_api(data)
        assert sub.fields is None


class TestInactiveSubscriber:
    def test_from_api_full_info(self):
        data = {"reason": 3, "reason_date": "2025/09/25 12:18:38", "email": "daniel@abirtone.com"}
        sub = InactiveSubscriber.from_api(data)
        assert sub.email == "daniel@abirtone.com"
        assert sub.reason == 3
        assert sub.reason_date == datetime(2025, 9, 25, 12, 18, 38)

    def test_from_api_email_only(self):
        data = {"email": "test@test.com"}
        sub = InactiveSubscriber.from_api(data)
        assert sub.email == "test@test.com"
        assert sub.reason is None
        assert sub.reason_date is None

    def test_reason_label_bounce(self):
        """BUG 3b: reason=1 es bounce (verificado cruzando 805 inactivos
        reales contra exports CSV; acumbamail-openapi.yaml lo documentaba
        al reves)."""
        sub = InactiveSubscriber.from_api({"email": "b@test.com", "reason": 1})
        assert sub.reason_label == InactiveReason.BOUNCE

    def test_reason_label_unsubscribed(self):
        """BUG 3b: reason=3 es baja voluntaria, no hard bounce."""
        sub = InactiveSubscriber.from_api({"email": "u@test.com", "reason": 3})
        assert sub.reason_label == InactiveReason.UNSUBSCRIBED

    def test_reason_label_unknown_code(self):
        sub = InactiveSubscriber.from_api({"email": "w@test.com", "reason": 42})
        assert sub.reason_label == InactiveReason.UNKNOWN

    def test_reason_label_missing_reason(self):
        sub = InactiveSubscriber.from_api({"email": "n@test.com"})
        assert sub.reason_label == InactiveReason.UNKNOWN


class TestSMTPWebhook:
    def test_from_api_parses_info_dict(self):
        data = {
            "info": {
                "url": "https://example.com/webhook",
                "soft_bounces": False,
                "complaints": False,
                "delivered": True,
                "active": False,
                "hard_bounces": True,
                "id": 87492,
                "opens": False,
                "clicks": False,
            }
        }
        wh = SMTPWebhook.from_api(data)
        assert wh.id == 87492
        assert wh.url == "https://example.com/webhook"
        assert wh.delivered is True
        assert wh.hard_bounces is True
        assert wh.soft_bounces is False
        assert wh.active is False
        assert wh.opens is False
        assert wh.clicks is False
        assert wh.complaints is False


class TestListWebhook:
    def test_from_api_parses_info_dict(self):
        data = {
            "info": {
                "url": "https://example.com/webhook",
                "soft_bounces": False,
                "complaints": False,
                "unsubscribes": True,
                "subscribes": True,
                "active": False,
                "hard_bounces": False,
                "id": 102650,
                "opens": False,
                "clicks": False,
            }
        }
        wh = ListWebhook.from_api(data)
        assert wh.id == 102650
        assert wh.url == "https://example.com/webhook"
        assert wh.subscribes is True
        assert wh.unsubscribes is True
        assert wh.hard_bounces is False
        assert wh.soft_bounces is False
        assert wh.active is False


class TestBatchSubscriberResult:
    def test_from_api_extracts_email_and_id(self):
        data = {"test@example.com": 5678672566}
        result = BatchSubscriberResult.from_api(data)
        assert result.email == "test@example.com"
        assert result.subscriber_id == 5678672566

    def test_from_api_handles_string_id(self):
        data = {"test@example.com": "9999999"}
        result = BatchSubscriberResult.from_api(data)
        assert result.subscriber_id == 9999999

    def test_from_api_defaults_status_to_added(self):
        result = BatchSubscriberResult.from_api({"test@example.com": 1})
        assert result.status == "added"
        assert result.error is None

    def test_from_api_nested_error_dict_already_exists(self):
        """BUG 2: forma real observada cuando el email ya existe en la lista."""
        data = {"dup@example.com": {"error": "Email already exists in this list"}}
        result = BatchSubscriberResult.from_api(data)
        assert result.email == "dup@example.com"
        assert result.subscriber_id is None
        assert result.status == "already_existed"
        assert result.error == "Email already exists in this list"

    def test_from_api_top_level_error_shape(self):
        data = {"error": {"email": "dup2@example.com", "message": "already exists"}}
        result = BatchSubscriberResult.from_api(data)
        assert result.email == "dup2@example.com"
        assert result.status == "already_existed"

    def test_from_api_unknown_shape_reports_failed_without_raising(self):
        result = BatchSubscriberResult.from_api({"x@test.com": {"weird": "shape"}})
        assert result.status in ("failed", "already_existed")
        assert result.subscriber_id is None

    def test_from_api_never_raises_on_garbage_input(self):
        result = BatchSubscriberResult.from_api("not-a-dict")
        assert result.status == "failed"
