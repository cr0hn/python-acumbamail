"""
Acumbamail SDK for Python.

This package provides a Python client for the Acumbamail API.
"""

from .client import AcumbamailClient
from .aclient import AsyncAcumbamailClient
from .automation_client import AutomationClient
from .automation_models import Automation, AutomationNode
from .exceptions import (
    AcumbamailError,
    AcumbamailRateLimitError,
    AcumbamailAPIError,
    AcumbamailValidationError,
)
from .models import (
    MailList,
    Subscriber,
    Campaign,
    CampaignClick,
    CampaignOpener,
    CampaignSoftBounce,
    Template,
    CampaignTotalInformation,
    SubscriberDetails,
    InactiveSubscriber,
    SMTPWebhook,
    ListWebhook,
    BatchSubscriberResult,
)

__version__ = "0.2.0"

__all__ = [
    "AcumbamailClient",
    "AsyncAcumbamailClient",
    "AcumbamailError",
    "AcumbamailRateLimitError",
    "AcumbamailAPIError",
    "AcumbamailValidationError",
    "MailList",
    "Subscriber",
    "Campaign",
    "CampaignClick",
    "CampaignOpener",
    "CampaignSoftBounce",
    "Template",
    "CampaignTotalInformation",
    "SubscriberDetails",
    "InactiveSubscriber",
    "SMTPWebhook",
    "ListWebhook",
    "BatchSubscriberResult",
    "AutomationClient",
    "Automation",
    "AutomationNode",
]
