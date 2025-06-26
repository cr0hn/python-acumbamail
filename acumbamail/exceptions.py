"""
Custom exceptions for the Acumbamail SDK.
"""

class AcumbamailError(Exception):
    """Base exception for all Acumbamail errors."""
    def __init__(self, message: str, response=None):
        super().__init__(message)
        self.response = response

class AcumbamailRateLimitError(AcumbamailError):
    """Raised when the API rate limit is exceeded."""
    pass

class AcumbamailAPIError(AcumbamailError):
    """Raised when the API returns an error."""
    pass

class AcumbamailValidationError(AcumbamailError):
    """Raised when the API request validation fails."""
    pass

__all__ = [
    "AcumbamailError",
    "AcumbamailRateLimitError",
    "AcumbamailAPIError",
    "AcumbamailValidationError"
] 