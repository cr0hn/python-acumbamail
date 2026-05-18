"""
Utility functions for the Acumbamail SDK.
"""


def manage_api_response_id(response) -> int:
    """
    Process and normalize the API response for ID extraction.

    This utility function is used to handle the different response formats returned by the Acumbamail API
    when creating or retrieving resources that have an integer ID. The function attempts to extract the
    integer ID from the response, whether the response is a string, integer, or dictionary containing an 'id' key.

    Args:
        response (Any): The API response, which can be a string, integer, or dictionary.

    Returns:
        int: The extracted integer ID from the response.

    Raises:
        ValueError: If the response type is not supported or the ID cannot be extracted.

    Example:
        >>> manage_api_response("12345")
        12345
        >>> manage_api_response(67890)
        67890
        >>> manage_api_response({"id": "54321"})
        54321
        >>> manage_api_response({"id": 98765})
        98765
        >>> manage_api_response(["not", "valid"])
        Traceback (most recent call last):
            ...
        ValueError: Invalid response type: <class 'list'>
    """
    if isinstance(response, (str, int)):
        return int(response)
    elif isinstance(response, dict):
        # "Unpop" the only item from the dictionary and return its value as int
        key, value = response.popitem()
        return int(value)
    else:
        raise ValueError(f"Invalid response type: {type(response)}")
