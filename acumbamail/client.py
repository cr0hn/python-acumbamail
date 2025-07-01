"""
Main client for the Acumbamail API.

This module provides a complete interface to interact with the Acumbamail API,
allowing you to manage mailing lists, campaigns, subscribers, and statistics.
"""

import time
import logging

from typing import List, Dict, Any, Optional
from datetime import datetime

import httpx

from .models import (
    CampaignTotalInformation,
    MailList, 
    Campaign, 
    Subscriber, 
    CampaignClick, 
    CampaignOpener, 
    CampaignSoftBounce,
    Template
)
from .exceptions import (
    AcumbamailError, 
    AcumbamailRateLimitError, 
    AcumbamailAPIError,
    AcumbamailValidationError
)

logger = logging.getLogger(__name__)

BASE_URL: str = "https://acumbamail.com/api/1/"

class AcumbamailClient:
    """
    Synchronous client for interacting with the Acumbamail API.
    
    This class provides a comprehensive interface to perform all available operations
    in the Acumbamail API, including mailing list management, campaign creation and
    management, subscriber operations, and detailed analytics and statistics.
    
    The client handles authentication, rate limiting, error processing, and response
    parsing automatically. It uses httpx for HTTP requests and provides a clean,
    Pythonic interface to the Acumbamail API.
    
    Attributes:
        auth_token (str): The API authentication token for Acumbamail
        base_url (str): Base URL for the Acumbamail API
        default_sender_name (str, optional): Default sender name for emails
        default_sender_email (str, optional): Default sender email for emails
        sender_company (str, optional): Company name for list creation
        sender_country (str, optional): Country code for list creation
    
    Example:
        Basic usage:
        >>> client = AcumbamailClient(auth_token='your-token')
        >>> lists = client.get_lists()
        >>> campaign = client.create_campaign(
        ...     name="Test Campaign",
        ...     subject="Hello!",
        ...     content="<p>Hi there!</p>",
        ...     list_ids=[1234],
        ...     from_name="John Doe",
        ...     from_email="john@example.com"
        ... )
        
        With default sender configuration:
        >>> client = AcumbamailClient(
        ...     auth_token='your-token',
        ...     default_sender_name="My Company",
        ...     default_sender_email="noreply@mycompany.com"
        ... )
        >>> campaign = client.create_campaign(
        ...     name="Newsletter",
        ...     subject="Monthly Update",
        ...     content="<h1>News</h1>",
        ...     list_ids=[1234]
        ... )
    """

    def __init__(
        self, 
        auth_token: str, 
        default_sender_name: str = None,
        default_sender_email: str = None,
        *,
        sender_company: str = None,
        sender_country: str = None
    ):
        """
        Initialize the Acumbamail client.
        
        Args:
            auth_token (str): Your Acumbamail API authentication token. This token
                is required for all API operations and can be obtained from your
                Acumbamail account dashboard.
            default_sender_name (str, optional): Default sender name to use for
                emails when not explicitly specified. This will be used as the
                "From" name in email campaigns and single emails.
            default_sender_email (str, optional): Default sender email address to
                use for emails when not explicitly specified. This must be a valid
                email address and will be used as the "From" email in campaigns.
            sender_company (str, optional): Company name to use when creating new
                mailing lists. This information is stored with the list metadata.
            sender_country (str, optional): Country code to use when creating new
                mailing lists. Defaults to "ES" if not specified. This should be
                a valid ISO country code (e.g., "US", "ES", "FR").
        
        Raises:
            AcumbamailValidationError: If the auth_token is empty or invalid
            
        Example:
            >>> # Basic initialization
            >>> client = AcumbamailClient(auth_token="abc123")
            
            >>> # With default sender information
            >>> client = AcumbamailClient(
            ...     auth_token="abc123",
            ...     default_sender_name="My Company",
            ...     default_sender_email="noreply@mycompany.com"
            ... )
            
            >>> # With company information for list creation
            >>> client = AcumbamailClient(
            ...     auth_token="abc123",
            ...     default_sender_email="noreply@mycompany.com",
            ...     sender_company="My Company Inc.",
            ...     sender_country="US"
            ... )
        """
        if not auth_token:
            raise AcumbamailValidationError("auth_token is required")
            
        self.auth_token = auth_token
        self.base_url = BASE_URL
        self.default_sender_name = default_sender_name
        self.default_sender_email = default_sender_email
        self.sender_company = sender_company
        self.sender_country = sender_country

    def _call_api(self, endpoint: str, data: Dict[str, Any] = None, max_retries: int = 3) -> Dict[str, Any]:
        """
        Make a call to the Acumbamail API.
        
        This method handles the API communication logic, including:
        - Authentication via token
        - Rate limit retry handling with exponential backoff
        - Error processing and exception mapping
        - JSON response conversion
        - HTTP client management
        
        Args:
            endpoint (str): API endpoint to call (e.g., "getLists", "createCampaign")
            data (Dict[str, Any], optional): Request data to send as JSON payload.
                If None, an empty dictionary will be used.
            max_retries (int, optional): Maximum number of retries for rate limit
                errors. Defaults to 3. Each retry waits progressively longer.
            
        Returns:
            Dict[str, Any]: Parsed JSON response from the API
            
        Raises:
            AcumbamailRateLimitError: When rate limit is exceeded and max retries
                have been reached
            AcumbamailAPIError: When the API returns an HTTP error (4xx, 5xx)
            AcumbamailValidationError: When the request is invalid (400 status)
            AcumbamailError: For other API errors, network issues, or JSON parsing
                failures
        
        Example:
            >>> response = client._call_api("getLists")
            >>> response = client._call_api("createList", {"name": "My List"})
        """
        if data is None:
            data = {}

        data.update({
            'auth_token': self.auth_token,
            'response_type': 'json'
        })

        url = f"{BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}/"
        retries = 0

        while retries < max_retries:
            try:
                with httpx.Client() as client:
                    response = client.post(url, json=data)

                if response.status_code == 429:
                    retries += 1
                    wait_time = 10 * retries
                    logger.warning(f"Rate limit exceeded. Waiting {wait_time} seconds. Retry {retries}/{max_retries}")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                if response.status_code == 429:
                    raise AcumbamailRateLimitError("Rate limit exceeded", response=response)
                elif response.status_code == 400:
                    raise AcumbamailValidationError(f"Invalid request: {response.text}", response=response)
                else:
                    raise AcumbamailAPIError(f"API error: {str(e)}", response=response)

            except httpx.RequestError as e:
                raise AcumbamailError(f"Request failed: {str(e)}")

            except ValueError as e:
                raise AcumbamailError(f"Invalid JSON response: {str(e)}", response=response)

        raise AcumbamailRateLimitError(f"Rate limit exceeded after {max_retries} retries")

    def get_lists(self) -> List[MailList]:
        """
        Retrieve all available mailing lists from your Acumbamail account.
        
        This method fetches all mailing lists and their associated statistics,
        including subscriber counts, bounce rates, and other metrics. The method
        makes multiple API calls to gather comprehensive information for each list.
        
        Note: This method includes a 1-second delay between API calls to avoid
        rate limiting issues.
        
        Returns:
            List[MailList]: A list of MailList objects, each containing:
                - List ID and basic information (name, description)
                - Subscriber statistics (total, unsubscribed, bounced)
                - Creation and update timestamps
                - Other list metadata
        
        Raises:
            AcumbamailAPIError: If the API request fails
            AcumbamailError: For other errors during the request
            
        Example:
            >>> lists = client.get_lists()
            >>> for mail_list in lists:
            ...     print(f"List: {mail_list.name} - {mail_list.subscribers_count} subscribers")
            ...     print(f"  Unsubscribed: {mail_list.unsubscribed_count}")
            ...     print(f"  Bounced: {mail_list.bounced_count}")
        """
        response = self._call_api("getLists")
        lists = []
        
        for list_id, list_data in response.items():
            # Get additional stats for each list
            stats = self._call_api("getListStats", {"list_id": list_id})
            list_data.update(stats)
            lists.append(MailList.from_api({**list_data, 'id': list_id}))
            time.sleep(1)  # Avoid rate limiting
            
        return lists

    def create_list(self, name: str, description: str = "") -> MailList:
        """
        Create a new mailing list in your Acumbamail account.
        
        This method creates a new mailing list with the specified name and
        description. The list will be associated with your account and can
        be used to store subscribers and send campaigns.
        
        Args:
            name (str): The name of the mailing list. This should be descriptive
                and meaningful to help you identify the list's purpose.
            description (str, optional): A detailed description of the mailing
                list's purpose, target audience, or any other relevant information.
                This helps with list organization and management.
            
        Returns:
            MailList: A MailList object representing the newly created list,
                containing the list ID and basic information.
            
        Raises:
            AcumbamailValidationError: If default_sender_email is not configured
                or if the name is empty
            AcumbamailAPIError: If the API request fails
            AcumbamailError: For other errors during the request
            
        Example:
            >>> # Create a basic list
            >>> new_list = client.create_list("Newsletter Subscribers")
            >>> print(f"Created list with ID: {new_list.id}")
            
            >>> # Create a list with description
            >>> marketing_list = client.create_list(
            ...     name="Marketing Campaigns",
            ...     description="List for promotional emails and special offers"
            ... )
            >>> print(f"Marketing list ID: {marketing_list.id}")
            
        Note:
            The default_sender_email must be configured either during client
            initialization or when calling this method, as it's required by
            the Acumbamail API for list creation.
        """
        if not self.default_sender_email:
            raise AcumbamailValidationError("default_sender_email is required for creating lists")
            
        if not name or not name.strip():
            raise AcumbamailValidationError("List name cannot be empty")
            
        data = {
            "name": name.strip(),
            "sender_email": self.default_sender_email,
            "description": description.strip()
        }
        
        if self.sender_company:
            data["company"] = self.sender_company

        if self.sender_country:
            data["country"] = self.sender_country

        response = self._call_api("createList", data)
        list_id = int(response)
        
        return MailList(
            id=list_id,
            name=name.strip(),
            description=description.strip()
        )

    def get_subscribers(self, list_id: int) -> List[Subscriber]:
        """
        Retrieve all subscribers from a specific mailing list.
        
        This method fetches all active subscribers from the specified mailing
        list, including their email addresses, custom fields, and subscription
        status information.
        
        Args:
            list_id (int): The unique identifier of the mailing list to fetch
                subscribers from. This ID can be obtained from the get_lists()
                method or when creating a new list.
            
        Returns:
            List[Subscriber]: A list of Subscriber objects, each containing:
                - Email address
                - List ID and subscription status
                - Custom fields and merge data
                - Subscription timestamp
                - Other subscriber metadata
        
        Raises:
            AcumbamailAPIError: If the API request fails or the list doesn't exist
            AcumbamailError: For other errors during the request
            
        Example:
            >>> # Get subscribers from a specific list
            >>> subscribers = client.get_subscribers(list_id=12345)
            >>> print(f"Found {len(subscribers)} subscribers")
            
            >>> # Process subscriber information
            >>> for subscriber in subscribers:
            ...     print(f"Email: {subscriber.email}")
            ...     print(f"Active: {subscriber.is_active}")
            ...     print(f"Fields: {subscriber.fields}")
            ...     if subscriber.subscribed_at:
            ...         print(f"Subscribed: {subscriber.subscribed_at}")
        
        Note:
            This method returns all subscribers in a single API call. For very
            large lists, consider implementing pagination or filtering if needed.
        """
        response = self._call_api("getSubscribers", {"list_id": list_id})
        return [
            Subscriber.from_api({**data, 'list_id': list_id, 'email': email})
            for email, data in response.items()
        ]

    def add_subscriber(self, email: str, list_id: int, fields: Dict[str, Any] = None) -> Subscriber:
        """
        Add a new subscriber to a mailing list.
        
        This method adds a subscriber to the specified mailing list with their
        email address and optional custom fields. The subscriber will be able
        to receive campaigns sent to that list.
        
        Args:
            email (str): The email address of the subscriber to add. This should
                be a valid email address format.
            list_id (int): The unique identifier of the mailing list to add the
                subscriber to. This ID can be obtained from get_lists() or when
                creating a new list.
            fields (Dict[str, Any], optional): Custom fields and merge data for
                the subscriber. These fields can be used in email campaigns for
                personalization. Common fields include:
                - "name": Subscriber's full name
                - "first_name": Subscriber's first name
                - "last_name": Subscriber's last name
                - "company": Subscriber's company
                - Any other custom fields defined for the list
            
        Returns:
            Subscriber: A Subscriber object representing the newly added subscriber,
                containing their email, list ID, and field information.
            
        Raises:
            AcumbamailValidationError: If the email format is invalid or required
                fields are missing
            AcumbamailAPIError: If the API request fails or the subscriber already
                exists in the list
            AcumbamailError: For other errors during the request
            
        Example:
            >>> # Add a basic subscriber
            >>> subscriber = client.add_subscriber(
            ...     email="john.doe@example.com",
            ...     list_id=12345
            ... )
            >>> print(f"Added subscriber: {subscriber.email}")
            
            >>> # Add subscriber with custom fields
            >>> subscriber = client.add_subscriber(
            ...     email="jane.smith@example.com",
            ...     list_id=12345,
            ...     fields={
            ...         "name": "Jane Smith",
            ...         "first_name": "Jane",
            ...         "last_name": "Smith",
            ...         "company": "Acme Corp",
            ...         "preferences": "weekly"
            ...     }
            ... )
            >>> print(f"Added {subscriber.fields['name']} to the list")
        
        Note:
            - If the subscriber already exists in the list, the API will return
              an error. You may want to check for existing subscribers first.
            - Custom fields must match the fields defined in your mailing list
              configuration for proper personalization in campaigns.
        """
        if not email or '@' not in email:
            raise AcumbamailValidationError("Invalid email address format")
            
        data = {
            "list_id": list_id,
            "merge_fields": {
                "email": email.lower().strip(),
                **(fields or {})
            }
        }
        
        self._call_api("addSubscriber", data)
        return Subscriber(email=email.lower().strip(), list_id=list_id, fields=fields)

    def delete_subscriber(self, email: str, list_id: int) -> None:
        """
        Remove a subscriber from a mailing list.
        
        This method permanently removes a subscriber from the specified mailing
        list. The subscriber will no longer receive campaigns sent to that list,
        and their data will be removed from the list's subscriber database.
        
        Args:
            email (str): The email address of the subscriber to remove. This
                should match the exact email address used when adding the
                subscriber to the list.
            list_id (int): The unique identifier of the mailing list to remove
                the subscriber from. This ID can be obtained from get_lists()
                or when creating a new list.
            
        Raises:
            AcumbamailValidationError: If the email format is invalid
            AcumbamailAPIError: If the API request fails or the subscriber
                doesn't exist in the list
            AcumbamailError: For other errors during the request
            
        Example:
            >>> # Remove a subscriber from a list
            >>> client.delete_subscriber(
            ...     email="john.doe@example.com",
            ...     list_id=12345
            ... )
            >>> print("Subscriber removed successfully")
            
            >>> # Remove multiple subscribers
            >>> emails_to_remove = ["user1@example.com", "user2@example.com"]
            >>> for email in emails_to_remove:
            ...     try:
            ...         client.delete_subscriber(email, list_id=12345)
            ...         print(f"Removed {email}")
            ...     except AcumbamailAPIError as e:
            ...         print(f"Failed to remove {email}: {e}")
        
        Note:
            - This operation is irreversible. The subscriber's data will be
              permanently deleted from the list.
            - If the subscriber doesn't exist in the list, the API will return
              an error.
            - Consider using unsubscribe functionality instead if you want to
              maintain subscriber history for compliance purposes.
        """
        if not email or '@' not in email:
            raise AcumbamailValidationError("Invalid email address format")
            
        data = {
            "list_id": list_id,
            "email": email.lower().strip()
        }
        self._call_api("deleteSubscriber", data)

    def get_list_stats(self, list_id: int) -> Dict[str, Any]:
        """
        Retrieve detailed statistics for a specific mailing list.
        
        This method fetches comprehensive statistics about a mailing list,
        including subscriber counts, engagement metrics, and campaign performance
        data associated with the list.
        
        Args:
            list_id (int): The unique identifier of the mailing list to get
                statistics for. This ID can be obtained from get_lists() or
                when creating a new list.
            
        Returns:
            Dict[str, Any]: A dictionary containing detailed list statistics:
                - total_subscribers (int): Total number of active subscribers
                - unsubscribed_subscribers (int): Number of unsubscribed users
                - hard_bounced_subscribers (int): Number of hard bounced emails
                - campaigns_sent (int): Number of campaigns sent to this list
                - Other list-specific metrics and metadata
        
        Raises:
            AcumbamailAPIError: If the API request fails or the list doesn't exist
            AcumbamailError: For other errors during the request
            
        Example:
            >>> # Get statistics for a specific list
            >>> stats = client.get_list_stats(list_id=12345)
            >>> print(f"Total subscribers: {stats['total_subscribers']}")
            >>> print(f"Unsubscribed: {stats['unsubscribed_subscribers']}")
            >>> print(f"Hard bounces: {stats['hard_bounced_subscribers']}")
            >>> print(f"Campaigns sent: {stats['campaigns_sent']}")
            
            >>> # Monitor list health
            >>> stats = client.get_list_stats(list_id=12345)
            >>> total = stats['total_subscribers']
            >>> bounces = stats['hard_bounced_subscribers']
            >>> bounce_rate = (bounces / total * 100) if total > 0 else 0
            >>> print(f"Bounce rate: {bounce_rate:.2f}%")
        
        Note:
            These statistics are real-time and reflect the current state of
            the mailing list. The data is updated after each campaign or
            subscriber operation.
        """
        return self._call_api("getListStats", {"list_id": list_id})

    def create_campaign(
        self,
        name: str,
        subject: str,
        content: str,
        list_ids: List[int],
        from_name: str = None,
        from_email: str = None,
        scheduled_at: datetime = None,
        tracking_enabled: bool = True,
    ) -> Campaign:
        """
        Create a new email campaign in your Acumbamail account.
        
        This method creates a new email campaign with the specified content and
        configuration. The campaign can be sent immediately or scheduled for a
        future date. The method automatically wraps the content with an
        unsubscribe footer to comply with email marketing regulations.
        
        Args:
            name (str): The name of the campaign. This is used for internal
                organization and appears in your Acumbamail dashboard.
            subject (str): The email subject line that recipients will see in
                their email client. This should be compelling and relevant to
                encourage opens.
            content (str): The HTML content of the email. This should be valid
                HTML and can include merge tags for personalization.
            list_ids (List[int]): List of mailing list IDs to send the campaign
                to. Multiple lists can be specified for broader distribution.
            from_name (str, optional): The sender name that will appear in the
                "From" field. If not specified, uses default_sender_name from
                client initialization.
            from_email (str, optional): The sender email address. If not specified,
                uses default_sender_email from client initialization.
            scheduled_at (datetime, optional): When to schedule the campaign for
                sending. If None, the campaign will be sent immediately.
            tracking_enabled (bool, optional): Whether to enable click and open
                tracking for the campaign. Defaults to True for better analytics.
            
        Returns:
            Campaign: A Campaign object representing the newly created campaign,
                containing the campaign ID and all configuration details.
            
        Raises:
            AcumbamailValidationError: If neither from_email nor default_sender_email
                is set, or if required fields are missing
            AcumbamailAPIError: If the API request fails
            AcumbamailError: For other errors during the request
            
        Example:
            >>> # Create a basic campaign
            >>> campaign = client.create_campaign(
            ...     name="Welcome Newsletter",
            ...     subject="Welcome to our community!",
            ...     content="<h1>Welcome!</h1><p>Thank you for joining us.</p>",
            ...     list_ids=[12345]
            ... )
            >>> print(f"Created campaign with ID: {campaign.id}")
            
            >>> # Create a scheduled campaign with tracking
            >>> from datetime import datetime, timedelta
            >>> scheduled_time = datetime.now() + timedelta(days=1)
            >>> campaign = client.create_campaign(
            ...     name="Weekly Newsletter",
            ...     subject="This week's updates",
            ...     content="<h1>Weekly Updates</h1><p>Here's what's new...</p>",
            ...     list_ids=[12345, 67890],
            ...     scheduled_at=scheduled_time,
            ...     pre_header="Stay updated with our latest news and offers"
            ... )
            >>> print(f"Scheduled campaign for: {campaign.scheduled_at}")
            
            >>> # Create campaign with custom sender
            >>> campaign = client.create_campaign(
            ...     name="Special Offer",
            ...     subject="Limited time offer - 50% off!",
            ...     content="<h1>Special Offer</h1><p>Don't miss out...</p>",
            ...     list_ids=[12345],
            ...     from_name="Sales Team",
            ...     from_email="sales@mycompany.com"
            ... )
        
        Note:
            - The content is automatically wrapped with an unsubscribe footer
              to comply with email marketing regulations.
            - If tracking is enabled, the campaign will track opens and clicks
              for analytics purposes.
            - Scheduled campaigns can be modified or cancelled before the
              scheduled time using the Acumbamail dashboard.
            - The campaign will be sent to all subscribers in the specified
              lists who are currently active.
        """
        if not from_email and not self.default_sender_email:
            raise AcumbamailValidationError("from_email or default_sender_email is required for creating campaigns")
            
        if not name or not name.strip():
            raise AcumbamailValidationError("Campaign name cannot be empty")
            
        if not subject or not subject.strip():
            raise AcumbamailValidationError("Campaign subject cannot be empty")
            
        if not content or not content.strip():
            raise AcumbamailValidationError("Campaign content cannot be empty")
            
        if not list_ids:
            raise AcumbamailValidationError("At least one list_id must be specified")
            
        if "*|UNSUBSCRIBE_URL|*" not in content:
            raise AcumbamailValidationError("Campaign content must contain the unsubscribe URL. You have to use the placeholder *|UNSUBSCRIBE_URL|*")

        campaign = Campaign(
            id=None,
            name=name.strip(),
            subject=subject.strip(),
            content=content,
            from_name=from_name or self.default_sender_name,
            from_email=from_email or self.default_sender_email,
            list_ids=list_ids,
            scheduled_at=scheduled_at,
            tracking_enabled=tracking_enabled
        )
        
        response = self._call_api("createCampaign", campaign.to_api_payload())
        campaign.id = int(response)
        
        return campaign

    def send_single_email(
        self,
        to_email: str,
        subject: str,
        content: str,
        from_name: str = None,
        from_email: str = None,
        category: str = ''
    ) -> int:
        """
        Send a single email to a specific recipient.
        
        This method sends an individual email to a single recipient. Unlike
        campaigns which are sent to mailing lists, this method is useful for
        transactional emails, notifications, or one-off communications.
        
        Args:
            to_email (str): The email address of the recipient. This should be
                a valid email address format.
            subject (str): The email subject line that the recipient will see
                in their email client.
            content (str): The HTML content of the email. This should be valid
                HTML and can include personalization.
            from_name (str, optional): The sender name that will appear in the
                "From" field. If not specified, uses default_sender_name from
                client initialization.
            from_email (str, optional): The sender email address. If not specified,
                uses default_sender_email from client initialization.
            category (str, optional): A category label for the email. This is
                useful for organizing and tracking different types of emails
                in your analytics.
            
        Returns:
            int: The unique identifier of the sent email. This ID can be used
                for tracking and reference purposes.
            
        Raises:
            AcumbamailValidationError: If neither from_email nor default_sender_email
                is set, or if the email format is invalid
            AcumbamailAPIError: If the API request fails
            AcumbamailError: For other errors during the request
            
        Example:
            >>> # Send a basic single email
            >>> email_id = client.send_single_email(
            ...     to_email="customer@example.com",
            ...     subject="Order Confirmation",
            ...     content="<h1>Thank you for your order!</h1><p>Order #12345</p>"
            ... )
            >>> print(f"Sent email with ID: {email_id}")
            
            >>> # Send email with custom sender and category
            >>> email_id = client.send_single_email(
            ...     to_email="support@example.com",
            ...     subject="New support ticket",
            ...     content="<h1>New Ticket</h1><p>Customer needs help...</p>",
            ...     from_name="Support System",
            ...     from_email="noreply@mycompany.com",
            ...     category="support_notification"
            ... )
            >>> print(f"Support notification sent: {email_id}")
            
            >>> # Send multiple individual emails
            >>> recipients = ["user1@example.com", "user2@example.com"]
            >>> for recipient in recipients:
            ...     try:
            ...         email_id = client.send_single_email(
            ...             to_email=recipient,
            ...             subject="Personal invitation",
            ...             content=f"<h1>Hello!</h1><p>You're invited, {recipient}</p>"
            ...         )
            ...         print(f"Sent to {recipient}: {email_id}")
            ...     except AcumbamailAPIError as e:
            ...         print(f"Failed to send to {recipient}: {e}")
        
        Note:
            - Single emails are sent immediately and cannot be scheduled.
            - Unlike campaigns, single emails are not tracked for opens/clicks
              by default, but delivery status can be monitored.
            - The recipient does not need to be subscribed to any mailing list
              to receive a single email.
            - Use this method for transactional emails, notifications, or
              one-off communications rather than marketing campaigns.
        """
        if not from_email and not self.default_sender_email:
            raise AcumbamailValidationError("from_email or default_sender_email is required for sending emails")
            
        if not to_email or '@' not in to_email:
            raise AcumbamailValidationError("Invalid recipient email address format")
            
        if not subject or not subject.strip():
            raise AcumbamailValidationError("Email subject cannot be empty")
            
        if not content or not content.strip():
            raise AcumbamailValidationError("Email content cannot be empty")
            
        data = {
            "from_name": from_name or self.default_sender_name,
            "from_email": from_email or self.default_sender_email,
            "to_email": to_email.lower().strip(),
            "subject": subject.strip(),
            "body": content.strip(),
            "category": category.strip(),
        }
        
        response = self._call_api("sendOne", data)
        return int(response)

    def get_campaign_basic_information(self, campaign_id: int) -> Dict[str, Any]:
        """
        Retrieve basic information about a specific campaign.
        
        This method fetches fundamental details about a campaign, including
        its configuration, status, and basic performance metrics. This is
        useful for getting a quick overview of a campaign without detailed
        analytics.
        
        Args:
            campaign_id (int): The unique identifier of the campaign to retrieve
                information for. This ID is returned when creating a campaign
                or can be obtained from get_campaigns().
            
        Returns:
            Dict[str, Any]: A dictionary containing basic campaign information:
                - Campaign name, subject, and content
                - Sender information (name, email)
                - Target lists and scheduling details
                - Basic status and delivery information
                - Other campaign metadata
        
        Raises:
            AcumbamailAPIError: If the API request fails or the campaign doesn't exist
            AcumbamailError: For other errors during the request
            
        Example:
            >>> # Get basic campaign information
            >>> campaign_info = client.get_campaign_basic_information(campaign_id=12345)
            >>> print(f"Campaign: {campaign_info['name']}")
            >>> print(f"Subject: {campaign_info['subject']}")
            >>> print(f"Status: {campaign_info.get('status', 'Unknown')}")
            
            >>> # Check campaign configuration
            >>> info = client.get_campaign_basic_information(campaign_id=12345)
            >>> print(f"From: {info['from_name']} <{info['from_email']}>")
            >>> print(f"Target lists: {info.get('lists', [])}")
            >>> print(f"Scheduled: {info.get('scheduled_at', 'Immediate')}")
        """
        return self._call_api("getCampaignBasicInformation", {"campaign_id": campaign_id})

    def get_campaign_clicks(self, campaign_id: int) -> List[CampaignClick]:
        """
        Retrieve detailed click statistics for a specific campaign.
        
        This method fetches comprehensive click data for all links included
        in the campaign, including total clicks, unique clicks, and click
        rates. This information is essential for understanding subscriber
        engagement and link performance.
        
        Args:
            campaign_id (int): The unique identifier of the campaign to get
                click statistics for. This ID is returned when creating a
                campaign or can be obtained from get_campaigns().
            
        Returns:
            List[CampaignClick]: A list of CampaignClick objects, each containing:
                - URL that was clicked
                - Total number of clicks
                - Number of unique clicks (unique subscribers)
                - Click rate as percentage of total recipients
                - Unique click rate as percentage of total recipients
        
        Raises:
            AcumbamailAPIError: If the API request fails or the campaign doesn't exist
            AcumbamailError: For other errors during the request
            
        Example:
            >>> # Get click statistics for a campaign
            >>> clicks = client.get_campaign_clicks(campaign_id=12345)
            >>> print(f"Found {len(clicks)} unique links clicked")
            
            >>> # Analyze link performance
            >>> for click in clicks:
            ...     print(f"URL: {click.url}")
            ...     print(f"  Total clicks: {click.clicks}")
            ...     print(f"  Unique clicks: {click.unique_clicks}")
            ...     print(f"  Click rate: {click.click_rate:.2%}")
            ...     print(f"  Unique click rate: {click.unique_click_rate:.2%}")
            
            >>> # Find best performing links
            >>> best_links = sorted(clicks, key=lambda x: x.unique_clicks, reverse=True)
            >>> print(f"Best performing link: {best_links[0].url}")
            >>> print(f"  Unique clicks: {best_links[0].unique_clicks}")
        
        Note:
            - Click tracking must be enabled on the campaign for this data
              to be available.
            - The data includes both total clicks (multiple clicks from the
              same subscriber) and unique clicks (one per subscriber).
            - Click rates are calculated as percentages of the total number
              of emails delivered.
        """
        response = self._call_api("getCampaignClicks", {"campaign_id": campaign_id})
        return [CampaignClick.from_api(data) for data in response]

    def get_campaign_information_by_isp(self, campaign_id: int) -> Dict[str, Any]:
        """
        Get campaign information grouped by ISP.
        
        Args:
            campaign_id (int): ID of the campaign
            
        Returns:
            Dict[str, Any]: Campaign statistics grouped by ISP
        """
        return self._call_api("getCampaignInformationByISP", {"campaign_id": campaign_id})

    def get_campaign_links(self, campaign_id: int) -> List[str]:
        """
        Get all links used in a campaign.
        
        Args:
            campaign_id (int): ID of the campaign
            
        Returns:
            List[str]: List of URLs used in the campaign
        """
        response = self._call_api("getCampaignLinks", {"campaign_id": campaign_id})
        return response

    def get_campaign_openers(self, campaign_id: int) -> List[CampaignOpener]:
        """
        Retrieve detailed information about who opened the campaign.
        
        This method fetches comprehensive data about subscribers who opened
        the email campaign, including their email addresses, opening times,
        and technical details about their devices and locations.
        
        Args:
            campaign_id (int): The unique identifier of the campaign to get
                opener information for. This ID is returned when creating a
                campaign or can be obtained from get_campaigns().
            
        Returns:
            List[CampaignOpener]: A list of CampaignOpener objects, each containing:
                - Subscriber's email address
                - Timestamp when the email was opened
                - IP address and location information
                - Browser and operating system details
                - Device type and user agent information
        
        Raises:
            AcumbamailAPIError: If the API request fails or the campaign doesn't exist
            AcumbamailError: For other errors during the request
            
        Example:
            >>> # Get opener information for a campaign
            >>> openers = client.get_campaign_openers(campaign_id=12345)
            >>> print(f"Found {len(openers)} unique opens")
            
            >>> # Analyze opener data
            >>> for opener in openers:
            ...     print(f"Email: {opener.email}")
            ...     print(f"  Opened at: {opener.opened_at}")
            ...     print(f"  Country: {opener.country}")
            ...     print(f"  Browser: {opener.browser}")
            ...     print(f"  OS: {opener.os}")
            ...     print(f"  Device: {opener.device}")
            
            >>> # Group by browser
            >>> browser_stats = {}
            >>> for opener in openers:
            ...     browser = opener.browser or "Unknown"
            ...     browser_stats[browser] = browser_stats.get(browser, 0) + 1
            
            >>> for browser, count in browser_stats.items():
            ...     print(f"{browser}: {count} opens")
        
        Note:
            - Open tracking must be enabled on the campaign for this data
              to be available.
            - Some email clients block tracking pixels, so actual opens
              may be higher than reported.
            - The data includes technical details that can help optimize
              email design for different devices and browsers.
        """
        response = self._call_api("getCampaignOpeners", {"campaign_id": campaign_id})
        return [CampaignOpener.from_api(data) for data in response]

    def get_campaign_openers_by_browser(self, campaign_id: int) -> Dict[str, int]:
        """
        Get statistics of openers grouped by browser.
        
        Args:
            campaign_id (int): ID of the campaign
            
        Returns:
            Dict[str, int]: Number of opens per browser
        """
        return self._call_api("getCampaignOpenersByBrowser", {"campaign_id": campaign_id})

    def get_campaign_openers_by_os(self, campaign_id: int) -> Dict[str, int]:
        """
        Get statistics of openers grouped by operating system.
        
        Args:
            campaign_id (int): ID of the campaign
            
        Returns:
            Dict[str, int]: Number of opens per operating system
        """
        return self._call_api("getCampaignOpenersByOs", {"campaign_id": campaign_id})

    def get_campaigns(self, complete_json: bool = False) -> List[Campaign]:
        """
        Get all campaigns.
        
        Args:
            complete_json (bool, optional): Whether to return complete campaign information
            
        Returns:
            List[Campaign]: List of campaign objects
        """
        response = self._call_api("getCampaigns", {"complete_json": 1 if complete_json else 0})
        return [Campaign.from_api(data) for data in response]

    def get_campaign_soft_bounces(self, campaign_id: int) -> List[CampaignSoftBounce]:
        """
        Get soft bounce information for a campaign.
        
        Args:
            campaign_id (int): ID of the campaign
            
        Returns:
            List[CampaignSoftBounce]: List of soft bounce events
        """
        response = self._call_api("getCampaignSoftBounces", {"campaign_id": campaign_id})
        return [CampaignSoftBounce.from_api(data) for data in response]

    def get_campaign_total_information(self, campaign_id: int) -> CampaignTotalInformation:
        """
        Retrieve comprehensive statistics for a specific campaign.
        
        This method fetches complete campaign performance data, including
        delivery statistics, engagement metrics, bounce rates, and overall
        campaign health indicators. This is the most comprehensive source
        of campaign analytics.
        
        Args:
            campaign_id (int): The unique identifier of the campaign to get
                total information for. This ID is returned when creating a
                campaign or can be obtained from get_campaigns().
            
        Returns:
            CampaignTotalInformation: An object containing comprehensive campaign
                statistics including:
                - Delivery metrics (total delivered, emails to send)
                - Engagement metrics (opened, unique clicks, total clicks)
                - Bounce information (hard bounces, soft bounces)
                - Unsubscribe and complaint counts
                - Campaign URL for viewing in Acumbamail dashboard
        
        Raises:
            AcumbamailAPIError: If the API request fails or the campaign doesn't exist
            AcumbamailError: For other errors during the request
            
        Example:
            >>> # Get comprehensive campaign statistics
            >>> stats = client.get_campaign_total_information(campaign_id=12345)
            >>> print(f"Campaign URL: {stats.campaign_url}")
            >>> print(f"Total delivered: {stats.total_delivered}")
            >>> print(f"Opened: {stats.opened}")
            >>> print(f"Unique clicks: {stats.unique_clicks}")
            >>> print(f"Hard bounces: {stats.hard_bounces}")
            >>> print(f"Unsubscribes: {stats.unsubscribes}")
            
            >>> # Calculate key metrics
            >>> if stats.total_delivered > 0:
            ...     open_rate = (stats.opened / stats.total_delivered) * 100
            ...     click_rate = (stats.unique_clicks / stats.total_delivered) * 100
            ...     bounce_rate = (stats.hard_bounces / stats.total_delivered) * 100
            ...     print(f"Open rate: {open_rate:.2f}%")
            ...     print(f"Click rate: {click_rate:.2f}%")
            ...     print(f"Bounce rate: {bounce_rate:.2f}%")
            
            >>> # Monitor campaign health
            >>> if stats.complaints > 0:
            ...     complaint_rate = (stats.complaints / stats.total_delivered) * 100
            ...     print(f"Complaint rate: {complaint_rate:.2f}%")
            ...     if complaint_rate > 0.1:
            ...         print("Warning: High complaint rate detected!")
        
        Note:
            - This method provides the most comprehensive view of campaign
              performance available through the API.
            - All metrics are calculated based on the total number of emails
              delivered, not just sent.
            - The campaign URL can be used to view detailed analytics in
              the Acumbamail web dashboard.
        """
        response = self._call_api("getCampaignTotalInformation", {"campaign_id": campaign_id})
        return CampaignTotalInformation.from_api(response)

    def get_stats_by_date(
        self, 
        list_id: int, 
        date_from: datetime, 
        date_to: datetime
    ) -> Dict[str, Dict[str, int]]:
        """
        Get statistics for a list within a date range.
        
        Args:
            list_id (int): ID of the mailing list
            date_from (datetime): Start date
            date_to (datetime): End date
            
        Returns:
            Dict[str, Dict[str, int]]: Daily statistics for the period
        """
        data = {
            "list_id": list_id,
            "date_from": date_from.strftime("%Y-%m-%d"),
            "date_to": date_to.strftime("%Y-%m-%d")
        }
        return self._call_api("getStatsByDate", data)

    def get_templates(self) -> List[Template]:
        """
        Get all email templates.
        
        Returns:
            List[Template]: List of available email templates
        """
        response = self._call_api("getTemplates")
        return [Template.from_api(data) for data in response]

    def get_list_fields(self, list_id: int) -> List[Dict[str, Any]]:
        """
        Get custom fields for a mailing list.
        
        Args:
            list_id (int): ID of the mailing list
            
        Returns:
            List[Dict[str, Any]]: List of custom fields and their configurations
        """
        return self._call_api("getListFields", {"list_id": list_id})

    def get_list_segments(self, list_id: int) -> List[Dict[str, Any]]:
        """
        Get segments for a mailing list.
        
        Args:
            list_id (int): ID of the mailing list
            
        Returns:
            List[Dict[str, Any]]: List of segments and their configurations
        """
        return self._call_api("getListSegments", {"list_id": list_id})

    def get_list_subs_stats(self, list_id: int) -> Dict[str, int]:
        """
        Get detailed subscriber statistics for a mailing list.
        
        Args:
            list_id (int): ID of the mailing list
            
        Returns:
            Dict[str, int]: Detailed subscriber statistics
        """
        return self._call_api("getListSubsStats", {"list_id": list_id})

    def get_merge_fields(self, list_id: int) -> List[Dict[str, Any]]:
        """
        Get merge fields for a mailing list.
        
        Args:
            list_id (int): ID of the mailing list
            
        Returns:
            List[Dict[str, Any]]: List of merge fields and their configurations
        """
        return self._call_api("getMergeFields", {"list_id": list_id}) 
    

__all__ = ("AcumbamailClient",)