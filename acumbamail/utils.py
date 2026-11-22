"""
Utility functions for the Acumbamail SDK.
"""

from typing import Any, Optional

from .exceptions import AcumbamailError


def _as_int(value: Any) -> Optional[int]:
    """Return int(value) if castable, else None (never raises)."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def parse_retry_after(response: Any, default_wait: float) -> float:
    """
    Compute how long to wait before retrying a 429 response.

    Respects the `Retry-After` header (seconds, per RFC 9110) when present
    and numeric; falls back to `default_wait` otherwise (the header can also
    be an HTTP-date, which we don't bother parsing since Acumbamail sends
    plain seconds in practice).
    """
    header = getattr(response, "headers", None)
    value = header.get("Retry-After") if header else None
    if value is not None:
        try:
            return max(float(value), 0.0)
        except (TypeError, ValueError):
            pass
    return default_wait


def manage_api_response_id(response: object) -> int:
    """
    Process and normalize the API response for ID extraction.

    This utility function handles the different response shapes returned by the
    Acumbamail API when creating or retrieving resources that have an integer ID:
    a bare string/int, or a dict keyed 'id' (createTemplate, createCampaign, ...),
    'list_id' (createList), 'subscriber_id', 'campaign_id', or any other key
    ending in '_id'.

    Args:
        response (Any): The API response, which can be a string, integer, or dictionary.

    Returns:
        int: The extracted integer ID from the response.

    Raises:
        ValueError: If the response type is not supported or the ID cannot be extracted.
            The message names the actual shape received, not a raw Python TypeError/ValueError.

    Example:
        >>> manage_api_response_id("12345")
        12345
        >>> manage_api_response_id(67890)
        67890
        >>> manage_api_response_id({"id": "54321"})
        54321
        >>> manage_api_response_id({"list_id": 456})
        456
        >>> manage_api_response_id({"subscriber_id": 789})
        789
        >>> manage_api_response_id(["not", "valid"])
        Traceback (most recent call last):
            ...
        ValueError: Invalid response type: <class 'list'>
    """
    if isinstance(response, (str, int)):
        return int(response)

    if isinstance(response, dict):
        if 'id' in response:
            return int(response['id'])

        id_keys = [key for key in response if isinstance(key, str) and key.endswith('_id')]
        if id_keys:
            return int(response[id_keys[0]])

        if len(response) == 1:
            key, value = next(iter(response.items()))
            if _as_int(value) is None:
                # Legacy: single-entry dict where the KEY itself is the ID,
                # e.g. {"54321": "some descriptive value"}.
                legacy_id = _as_int(key)
                if legacy_id is not None:
                    return legacy_id

        raise ValueError(
            "Cannot extract an integer ID from the API response: expected an 'id' "
            f"key, a key ending in '_id', or a single-entry legacy dict; got {response!r}"
        )

    raise ValueError(f"Invalid response type: {type(response)}")


def ensure_dict(value: object) -> dict[str, Any]:
    """Return ``value`` if the API sent a JSON object, else raise (the shape is untrusted)."""
    if not isinstance(value, dict):
        raise AcumbamailError(f"Expected a JSON object from the API, got {type(value).__name__}")
    return value


def ensure_list(value: object) -> list[Any]:
    """Return ``value`` if the API sent a JSON array, else raise (the shape is untrusted)."""
    if not isinstance(value, list):
        raise AcumbamailError(f"Expected a JSON array from the API, got {type(value).__name__}")
    return value
