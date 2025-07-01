"""
Async client for the Acumbamail API.

This module provides an asynchronous interface to interact with the Acumbamail API,
allowing you to manage mailing lists, campaigns, subscribers, and statistics
using async/await patterns.
"""

import asyncio
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

class AsyncAcumbamailClient:
    """
    Asynchronous client for interacting with the Acumbamail API.
    
    This class provides an async interface to perform all available operations
    in the Acumbamail API, including mailing list management, campaign creation
    and management, subscriber operations, and detailed analytics and statistics.
    
    The client handles authentication, rate limiting, error processing, and response
    parsing automatically. It uses httpx for HTTP requests and provides a clean,
    async/await interface to the Acumbamail API. This client is ideal for applications
    that need to handle multiple API calls concurrently or integrate with async
    frameworks like FastAPI, aiohttp, or asyncio-based applications.
    
    The client supports both context manager usage (recommended) and manual
    initialization/closing patterns.
    
    Attributes:
        auth_token (str): The API authentication token for Acumbamail
        base_url (str): Base URL for the Acumbamail API
        default_sender_name (str, optional): Default sender name for emails
        default_sender_email (str, optional): Default sender email for emails
        sender_company (str, optional): Company name for list creation
        sender_country (str, optional): Country code for list creation
        timeout (float): Request timeout in seconds
        _client (Optional[httpx.AsyncClient]): Internal HTTP client instance
    
    Example:
        Using context manager (recommended):
        >>> async with AsyncAcumbamailClient(auth_token='your-token') as client:
        ...     lists = await client.get_lists()
        ...     campaign = await client.create_campaign(
        ...         name="Test Campaign",
        ...         subject="Hello!",
        ...         content="<p>Hi there!</p>",
        ...         list_ids=[1234],
        ...         from_name="John Doe",
        ...         from_email="john@example.com"
        ...     )
        
        Manual initialization:
        >>> client = AsyncAcumbamailClient(auth_token='your-token')
        >>> try:
        ...     lists = await client.get_lists()
        ... finally:
        ...     await client.close()
        
        With default sender configuration:
        >>> async with AsyncAcumbamailClient(
        ...     auth_token='your-token',
        ...     default_sender_name="My Company",
        ...     default_sender_email="noreply@mycompany.com",
        ...     timeout=60.0
        ... ) as client:
        ...     campaign = await client.create_campaign(
        ...         name="Newsletter",
        ...         subject="Monthly Update",
        ...         content="<h1>News</h1>",
        ...         list_ids=[1234]
        ...     )
        
        Concurrent operations:
        >>> async with AsyncAcumbamailClient(auth_token='your-token') as client:
        ...     # Run multiple operations concurrently
        ...     lists_task = client.get_lists()
        ...     templates_task = client.get_templates()
        ...     campaigns_task = client.get_campaigns()
        ...     
        ...     # Wait for all to complete
        ...     lists, templates, campaigns = await asyncio.gather(
        ...         lists_task, templates_task, campaigns_task
        ...     )
    """

    def __init__(
        self, 
        auth_token: str, 
        default_sender_name: str = None,
        default_sender_email: str = None,
        *,
        sender_company: str = None,
        sender_country: str = None,
        timeout: float = 30.0
    ):
        """
        Initialize the async Acumbamail client.
        
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
            timeout (float, optional): Request timeout in seconds. Defaults to 30.0.
                This timeout applies to individual API requests.
        
        Raises:
            AcumbamailValidationError: If the auth_token is empty or invalid
            
        Example:
            >>> # Basic initialization
            >>> client = AsyncAcumbamailClient(auth_token="abc123")
            
            >>> # With default sender information
            >>> client = AsyncAcumbamailClient(
            ...     auth_token="abc123",
            ...     default_sender_name="My Company",
            ...     default_sender_email="noreply@mycompany.com"
            ... )
            
            >>> # With company information and custom timeout
            >>> client = AsyncAcumbamailClient(
            ...     auth_token="abc123",
            ...     default_sender_email="noreply@mycompany.com",
            ...     sender_company="My Company Inc.",
            ...     sender_country="US",
            ...     timeout=60.0
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
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """
        Async context manager entry point.
        
        Initializes the HTTP client when entering the context manager.
        This is the recommended way to use the async client as it ensures
        proper resource cleanup.
        
        Returns:
            AsyncAcumbamailClient: The client instance ready for use
            
        Example:
            >>> async with AsyncAcumbamailClient(auth_token="abc123") as client:
            ...     lists = await client.get_lists()
        """
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit point.
        
        Ensures the HTTP client is properly closed when exiting the context
        manager, even if an exception occurs.
        
        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred
        """
        if self._client:
            await self._client.aclose()

    async def _call_api(self, endpoint: str, data: Dict[str, Any] = None, max_retries: int = 3) -> Dict[str, Any]:
        """
        Make an async call to the Acumbamail API.
        
        This method handles the API communication logic, including:
        - Authentication via token
        - Rate limit retry handling with exponential backoff
        - Error processing and exception mapping
        - JSON response conversion
        - Async HTTP client management
        
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
            >>> response = await client._call_api("getLists")
            >>> response = await client._call_api("createList", {"name": "My List"})
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
                if not self._client:
                    raise AcumbamailError("Client not initialized. Use async context manager or call _ensure_client()")

                response = await self._client.post(url, json=data)

                if response.status_code == 429:
                    retries += 1
                    wait_time = 10 * retries
                    logger.warning(f"Rate limit exceeded. Waiting {wait_time} seconds. Retry {retries}/{max_retries}")
                    await asyncio.sleep(wait_time)
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

    async def _ensure_client(self):
        """
        Ensure the HTTP client is initialized.
        
        This method creates the HTTP client if it doesn't exist. It's called
        automatically by all public methods, but can be called manually if
        needed when not using the context manager.
        
        Example:
            >>> client = AsyncAcumbamailClient(auth_token="abc123")
            >>> await client._ensure_client()
            >>> lists = await client.get_lists()
        """
        if not self._client:
            self._client = httpx.AsyncClient(timeout=self.timeout)

    async def close(self):
        """
        Close the HTTP client and free resources.
        
        This method should be called when you're done using the client,
        especially when not using the context manager. It ensures that
        the underlying HTTP client is properly closed and resources are
        freed.
        
        Example:
            >>> client = AsyncAcumbamailClient(auth_token="abc123")
            >>> try:
            ...     lists = await client.get_lists()
            ... finally:
            ...     await client.close()
        """
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get_lists(self) -> List[MailList]:
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
            >>> # Get all lists
            >>> lists = await client.get_lists()
            >>> print(f"Found {len(lists)} lists")
            
            >>> # Process list information
            >>> for mail_list in lists:
            ...     print(f"List: {mail_list.name} - {mail_list.subscribers_count} subscribers")
            ...     print(f"  Unsubscribed: {mail_list.unsubscribed_count}")
            ...     print(f"  Bounced: {mail_list.bounced_count}")
            
            >>> # Find lists with high bounce rates
            >>> high_bounce_lists = [
            ...     lst for lst in lists 
            ...     if lst.subscribers_count > 0 and (lst.bounced_count / lst.subscribers_count) > 0.05
            ... ]
            >>> print(f"Lists with high bounce rates: {len(high_bounce_lists)}")
        """
        await self._ensure_client()
        response = await self._call_api("getLists")
        lists = []
        
        for list_id, list_data in response.items():
            # Get additional stats for each list
            stats = await self._call_api("getListStats", {"list_id": list_id})
            list_data.update(stats)
            lists.append(MailList.from_api({**list_data, 'id': list_id}))
            await asyncio.sleep(1)  # Avoid rate limiting
            
        return lists

    async def create_list(self, name: str, description: str = "") -> MailList:
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
            >>> new_list = await client.create_list("Newsletter Subscribers")
            >>> print(f"Created list with ID: {new_list.id}")
            
            >>> # Create a list with description
            >>> marketing_list = await client.create_list(
            ...     name="Marketing Campaigns",
            ...     description="List for promotional emails and special offers"
            ... )
            >>> print(f"Marketing list ID: {marketing_list.id}")
            
            >>> # Create multiple lists concurrently
            >>> list_configs = [
            ...     ("Newsletter", "Weekly newsletter subscribers"),
            ...     ("Promotions", "Special offers and promotions"),
            ...     ("Updates", "Product updates and announcements")
            ... ]
            >>> 
            >>> tasks = [
            ...     client.create_list(name, description) 
            ...     for name, description in list_configs
            ... ]
            >>> lists = await asyncio.gather(*tasks)
            >>> print(f"Created {len(lists)} lists")
        
        Note:
            The default_sender_email must be configured either during client
            initialization or when calling this method, as it's required by
            the Acumbamail API for list creation.
        """
        await self._ensure_client()
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

        response = await self._call_api("createList", data)
        list_id = int(response)
        
        return MailList(
            id=list_id,
            name=name.strip(),
            description=description.strip()
        )

    async def get_subscribers(self, list_id: int) -> List[Subscriber]:
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
            >>> subscribers = await client.get_subscribers(list_id=12345)
            >>> print(f"Found {len(subscribers)} subscribers")
            
            >>> # Process subscriber information
            >>> for subscriber in subscribers:
            ...     print(f"Email: {subscriber.email}")
            ...     print(f"Active: {subscriber.is_active}")
            ...     print(f"Fields: {subscriber.fields}")
            ...     if subscriber.subscribed_at:
            ...         print(f"Subscribed: {subscriber.subscribed_at}")
            
            >>> # Filter subscribers by custom fields
            >>> premium_subscribers = [
            ...     s for s in subscribers 
            ...     if s.fields.get('membership_type') == 'premium'
            ... ]
            >>> print(f"Premium subscribers: {len(premium_subscribers)}")
        
        Note:
            This method returns all subscribers in a single API call. For very
            large lists, consider implementing pagination or filtering if needed.
        """
        await self._ensure_client()
        response = await self._call_api("getSubscribers", {"list_id": list_id})
        return [
            Subscriber.from_api({**data, 'list_id': list_id, 'email': email})
            for email, data in response.items()
        ]

    async def add_subscriber(self, email: str, list_id: int, fields: Dict[str, Any] = None) -> Subscriber:
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
            >>> subscriber = await client.add_subscriber(
            ...     email="john.doe@example.com",
            ...     list_id=12345
            ... )
            >>> print(f"Added subscriber: {subscriber.email}")
            
            >>> # Add subscriber with custom fields
            >>> subscriber = await client.add_subscriber(
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
            
            >>> # Add multiple subscribers concurrently
            >>> subscribers_data = [
            ...     ("user1@example.com", {"name": "User One"}),
            ...     ("user2@example.com", {"name": "User Two"}),
            ...     ("user3@example.com", {"name": "User Three"})
            ... ]
            >>> 
            >>> tasks = [
            ...     client.add_subscriber(email, list_id=12345, fields=fields)
            ...     for email, fields in subscribers_data
            ... ]
            >>> subscribers = await asyncio.gather(*tasks)
            >>> print(f"Added {len(subscribers)} subscribers")
        
        Note:
            - If the subscriber already exists in the list, the API will return
              an error. You may want to check for existing subscribers first.
            - Custom fields must match the fields defined in your mailing list
              configuration for proper personalization in campaigns.
        """
        await self._ensure_client()
        if not email or '@' not in email:
            raise AcumbamailValidationError("Invalid email address format")
            
        data = {
            "list_id": list_id,
            "merge_fields": {
                "email": email.lower().strip(),
                **(fields or {})
            }
        }
        
        await self._call_api("addSubscriber", data)
        return Subscriber(email=email.lower().strip(), list_id=list_id, fields=fields)

    async def delete_subscriber(self, email: str, list_id: int) -> None:
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
            >>> await client.delete_subscriber(
            ...     email="john.doe@example.com",
            ...     list_id=12345
            ... )
            >>> print("Subscriber removed successfully")
            
            >>> # Remove multiple subscribers concurrently
            >>> emails_to_remove = ["user1@example.com", "user2@example.com"]
            >>> tasks = [
            ...     client.delete_subscriber(email, list_id=12345)
            ...     for email in emails_to_remove
            ... ]
            >>> await asyncio.gather(*tasks)
            >>> print(f"Removed {len(emails_to_remove)} subscribers")
            
            >>> # Remove subscribers with error handling
            >>> emails_to_remove = ["user1@example.com", "user2@example.com"]
            >>> for email in emails_to_remove:
            ...     try:
            ...         await client.delete_subscriber(email, list_id=12345)
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
        await self._ensure_client()
        if not email or '@' not in email:
            raise AcumbamailValidationError("Invalid email address format")
            
        data = {
            "list_id": list_id,
            "email": email.lower().strip()
        }
        await self._call_api("deleteSubscriber", data)

    async def get_list_stats(self, list_id: int) -> Dict[str, Any]:
        """
        Get statistics for a specific list.
        
        Args:
            list_id (int): ID of the mailing list
            
        Returns:
            Dict[str, Any]: Dictionary with list statistics including:
                - total_subscribers
                - unsubscribed_subscribers
                - hard_bounced_subscribers
                - campaigns_sent
        """
        await self._ensure_client()
        return await self._call_api("getListStats", {"list_id": list_id})

    async def create_campaign(
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
        Create a new email campaign.
        
        Args:
            name (str): Name of the campaign
            subject (str): Email subject
            content (str): HTML content of the email
            list_ids (List[int]): List of mailing list IDs to send to
            from_name (str, optional): Sender name. Defaults to default_sender_name
            from_email (str, optional): Sender email. Defaults to default_sender_email
            scheduled_at (datetime, optional): When to schedule the campaign
            tracking_enabled (bool, optional): Whether to enable tracking. Defaults to True
            
        Returns:
            Campaign: Object representing the created campaign
            
        Raises:
            AcumbamailValidationError: If neither from_email nor default_sender_email is set
        """
        await self._ensure_client()
        if not list_ids:
            raise AcumbamailValidationError("At least one list_id must be specified")
            
        if "*|UNSUBSCRIBE_URL|*" not in content:
            raise AcumbamailValidationError("Campaign content must contain the unsubscribe URL. You have to use the placeholder *|UNSUBSCRIBE_URL|*")

        if not from_email and not self.default_sender_email:
            raise AcumbamailValidationError("from_email or default_sender_email is required for creating campaigns")
            
        campaign = Campaign(
            id=None,
            name=name,
            subject=subject,
            content=content,
            from_name=from_name or self.default_sender_name,
            from_email=from_email or self.default_sender_email,
            list_ids=list_ids,
            scheduled_at=scheduled_at,
            tracking_enabled=tracking_enabled
        )
        
        response = await self._call_api("createCampaign", campaign.to_api_payload())
        campaign.id = int(response)
        
        return campaign

    async def send_single_email(
        self,
        to_email: str,
        subject: str,
        content: str,
        from_name: str = None,
        from_email: str = None,
        category: str = ''
    ) -> int:
        """
        Send a single email.
        
        Args:
            to_email (str): Recipient email address
            subject (str): Email subject
            content (str): HTML content of the email
            from_name (str, optional): Sender name. Defaults to default_sender_name
            from_email (str, optional): Sender email. Defaults to default_sender_email
            category (str, optional): Email category for tracking
            
        Returns:
            int: ID of the sent email
            
        Raises:
            AcumbamailValidationError: If neither from_email nor default_sender_email is set
        """
        await self._ensure_client()
        if not from_email and not self.default_sender_email:
            raise AcumbamailValidationError("from_email or default_sender_email is required for sending emails")
            
        data = {
            "from_name": from_name or self.default_sender_name,
            "from_email": from_email or self.default_sender_email,
            "to_email": to_email,
            "subject": subject,
            "body": content,
            "category": category,
        }
        
        response = await self._call_api("sendOne", data)
        return int(response)

    async def get_campaign_basic_information(self, campaign_id: int) -> Dict[str, Any]:
        """
        Get basic information about a campaign.
        
        Args:
            campaign_id (int): ID of the campaign
            
        Returns:
            Dict[str, Any]: Basic campaign information
        """
        await self._ensure_client()
        return await self._call_api("getCampaignBasicInformation", {"campaign_id": campaign_id})

    async def get_campaign_clicks(self, campaign_id: int) -> List[CampaignClick]:
        """
        Get click statistics for a campaign.
        
        Args:
            campaign_id (int): ID of the campaign
            
        Returns:
            List[CampaignClick]: List of click events with statistics
        """
        await self._ensure_client()
        response = await self._call_api("getCampaignClicks", {"campaign_id": campaign_id})
        return [CampaignClick.from_api(data) for data in response]

    async def get_campaign_information_by_isp(self, campaign_id: int) -> Dict[str, Any]:
        """
        Get campaign information grouped by ISP.
        
        Args:
            campaign_id (int): ID of the campaign
            
        Returns:
            Dict[str, Any]: Campaign statistics grouped by ISP
        """
        await self._ensure_client()
        return await self._call_api("getCampaignInformationByISP", {"campaign_id": campaign_id})

    async def get_campaign_links(self, campaign_id: int) -> List[str]:
        """
        Get all links used in a campaign.
        
        Args:
            campaign_id (int): ID of the campaign
            
        Returns:
            List[str]: List of URLs used in the campaign
        """
        await self._ensure_client()
        response = await self._call_api("getCampaignLinks", {"campaign_id": campaign_id})
        return response

    async def get_campaign_openers(self, campaign_id: int) -> List[CampaignOpener]:
        """
        Get information about who opened the campaign.
        
        Args:
            campaign_id (int): ID of the campaign
            
        Returns:
            List[CampaignOpener]: List of open events with subscriber information
        """
        await self._ensure_client()
        response = await self._call_api("getCampaignOpeners", {"campaign_id": campaign_id})
        return [CampaignOpener.from_api(data) for data in response]

    async def get_campaign_openers_by_browser(self, campaign_id: int) -> Dict[str, int]:
        """
        Get statistics of openers grouped by browser.
        
        Args:
            campaign_id (int): ID of the campaign
            
        Returns:
            Dict[str, int]: Number of opens per browser
        """
        await self._ensure_client()
        return await self._call_api("getCampaignOpenersByBrowser", {"campaign_id": campaign_id})

    async def get_campaign_openers_by_os(self, campaign_id: int) -> Dict[str, int]:
        """
        Get statistics of openers grouped by operating system.
        
        Args:
            campaign_id (int): ID of the campaign
            
        Returns:
            Dict[str, int]: Number of opens per operating system
        """
        await self._ensure_client()
        return await self._call_api("getCampaignOpenersByOs", {"campaign_id": campaign_id})

    async def get_campaigns(self, complete_json: bool = False) -> List[Campaign]:
        """
        Get all campaigns.
        
        Args:
            complete_json (bool, optional): Whether to return complete campaign information
            
        Returns:
            List[Campaign]: List of campaign objects
        """
        await self._ensure_client()
        response = await self._call_api("getCampaigns", {"complete_json": 1 if complete_json else 0})
        return [Campaign.from_api(data) for data in response]

    async def get_campaign_soft_bounces(self, campaign_id: int) -> List[CampaignSoftBounce]:
        """
        Get soft bounce information for a campaign.
        
        Args:
            campaign_id (int): ID of the campaign
            
        Returns:
            List[CampaignSoftBounce]: List of soft bounce events
        """
        await self._ensure_client()
        response = await self._call_api("getCampaignSoftBounces", {"campaign_id": campaign_id})
        return [CampaignSoftBounce.from_api(data) for data in response]

    async def get_campaign_total_information(self, campaign_id: int) -> CampaignTotalInformation:
        """
        Get total statistics for a campaign.
        
        Args:
            campaign_id (int): ID of the campaign
            
        Returns:
            CampaignTotalInformation: Complete campaign statistics
        """
        await self._ensure_client()
        response = await self._call_api("getCampaignTotalInformation", {"campaign_id": campaign_id})
        return CampaignTotalInformation.from_api(response)

    async def get_stats_by_date(
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
        await self._ensure_client()
        data = {
            "list_id": list_id,
            "date_from": date_from.strftime("%Y-%m-%d"),
            "date_to": date_to.strftime("%Y-%m-%d")
        }
        return await self._call_api("getStatsByDate", data)

    async def get_templates(self) -> List[Template]:
        """
        Get all email templates.
        
        Returns:
            List[Template]: List of available email templates
        """
        await self._ensure_client()
        response = await self._call_api("getTemplates")
        return [Template.from_api(data) for data in response]

    async def get_list_fields(self, list_id: int) -> List[Dict[str, Any]]:
        """
        Get custom fields for a mailing list.
        
        Args:
            list_id (int): ID of the mailing list
            
        Returns:
            List[Dict[str, Any]]: List of custom fields and their configurations
        """
        await self._ensure_client()
        return await self._call_api("getListFields", {"list_id": list_id})

    async def get_list_segments(self, list_id: int) -> List[Dict[str, Any]]:
        """
        Get segments for a mailing list.
        
        Args:
            list_id (int): ID of the mailing list
            
        Returns:
            List[Dict[str, Any]]: List of segments and their configurations
        """
        await self._ensure_client()
        return await self._call_api("getListSegments", {"list_id": list_id})

    async def get_list_subs_stats(self, list_id: int) -> Dict[str, int]:
        """
        Get detailed subscriber statistics for a mailing list.
        
        Args:
            list_id (int): ID of the mailing list
            
        Returns:
            Dict[str, int]: Detailed subscriber statistics
        """
        await self._ensure_client()
        return await self._call_api("getListSubsStats", {"list_id": list_id})

    async def get_merge_fields(self, list_id: int) -> List[Dict[str, Any]]:
        """
        Get merge fields for a mailing list.
        
        Args:
            list_id (int): ID of the mailing list
            
        Returns:
            List[Dict[str, Any]]: List of merge fields and their configurations
        """
        await self._ensure_client()
        return await self._call_api("getMergeFields", {"list_id": list_id})


__all__ = ("AsyncAcumbamailClient",) 