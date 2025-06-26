"""
Data models for the Acumbamail SDK.

This module contains all the data models used to interact with the Acumbamail API.
Each model represents a different entity in the Acumbamail system and includes methods
to convert between API responses and Python objects.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any

@dataclass
class MailList:
    """
    Represents a mailing list in Acumbamail.
    
    Attributes:
        id (int): Unique identifier of the mailing list
        name (str): Name of the mailing list
        description (str): Description of the mailing list
        subscribers_count (int): Total number of active subscribers
        unsubscribed_count (int): Number of unsubscribed users
        bounced_count (int): Number of hard bounced emails
        created_at (Optional[datetime]): Creation timestamp
        updated_at (Optional[datetime]): Last update timestamp
    """
    id: int
    name: str
    description: str
    subscribers_count: int = 0
    unsubscribed_count: int = 0
    bounced_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'MailList':
        """
        Create a MailList instance from API response data.
        
        Args:
            data (Dict[str, Any]): Raw API response data
            
        Returns:
            MailList: A new MailList instance
            
        Example:
            >>> data = {
            ...     'id': 123,
            ...     'name': 'My List',
            ...     'description': 'Test list',
            ...     'total_subscribers': 100
            ... }
            >>> MailList.from_api(data)
            MailList(id=123, name='My List', description='Test list', ...)
        """
        return cls(
            id=int(data['id']),
            name=data['name'],
            description=data.get('description', ''),
            subscribers_count=int(data.get('total_subscribers', 0)),
            unsubscribed_count=int(data.get('unsubscribed_subscribers', 0)),
            bounced_count=int(data.get('hard_bounced_subscribers', 0))
        )

@dataclass
class Subscriber:
    """
    Represents a subscriber in Acumbamail.
    
    Attributes:
        email (str): Subscriber's email address
        list_id (int): ID of the mailing list they're subscribed to
        is_active (bool): Whether the subscription is active
        fields (Dict[str, Any]): Custom fields for the subscriber
        subscribed_at (Optional[datetime]): Subscription timestamp
    """
    email: str
    list_id: int
    is_active: bool = True
    fields: Dict[str, Any] = None
    subscribed_at: Optional[datetime] = None

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'Subscriber':
        """
        Create a Subscriber instance from API response data.
        
        Args:
            data (Dict[str, Any]): Raw API response data
            
        Returns:
            Subscriber: A new Subscriber instance
        """
        return cls(
            email=data['email'],
            list_id=int(data['list_id']),
            is_active=data.get('active', True),
            fields=data.get('merge_fields', {}),
            subscribed_at=datetime.fromisoformat(data['subscribed_at']) if 'subscribed_at' in data else None
        )

@dataclass
class Campaign:
    """
    Represents an email campaign in Acumbamail.
    
    Attributes:
        id (Optional[int]): Campaign ID (None for new campaigns)
        name (str): Campaign name
        subject (str): Email subject line
        content (str): HTML content of the email
        from_name (str): Sender name
        from_email (str): Sender email address
        list_ids (List[int]): IDs of target mailing lists
        scheduled_at (Optional[datetime]): When to send the campaign
        sent_at (Optional[datetime]): When the campaign was sent
        tracking_enabled (bool): Whether to track opens/clicks
        pre_header (Optional[str]): Preview text shown in email clients
        stats (Dict[str, Any]): Campaign statistics
    """
    id: Optional[int]
    name: str
    subject: str
    content: str
    from_name: str
    from_email: str
    list_ids: List[int]
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    tracking_enabled: bool = True
    pre_header: Optional[str] = None
    stats: Dict[str, Any] = None

    def to_api_payload(self) -> Dict[str, Any]:
        """
        Convert the campaign to an API request payload.
        
        Returns:
            Dict[str, Any]: Data formatted for API submission
            
        Example:
            >>> campaign = Campaign(name="Test", subject="Hello", ...)
            >>> payload = campaign.to_api_payload()
            >>> print(payload)
            {
                'name': 'Test',
                'subject': 'Hello',
                'tracking_urls': 1,
                ...
            }
        """
        payload = {
            "name": self.name,
            "from_name": self.from_name,
            "from_email": self.from_email,
            "lists": self.list_ids,
            "content": self.content,
            "subject": self.subject,
            "tracking_urls": 1 if self.tracking_enabled else 0,
            "complete_json": 1,
        }

        if self.scheduled_at:
            payload["date_send"] = self.scheduled_at.strftime("%Y-%m-%d %H:%M")
            
        if self.pre_header:
            payload["pre_header"] = self.pre_header

        return payload

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'Campaign':
        """
        Create a Campaign instance from API response data.
        
        Args:
            data (Dict[str, Any]): Raw API response data
            
        Returns:
            Campaign: A new Campaign instance
        """
        return cls(
            id=int(data['id']),
            name=data['name'],
            subject=data['subject'],
            content=data['content'],
            from_name=data['from_name'],
            from_email=data['from_email'],
            list_ids=[int(id_) for id_ in data['lists']],
            sent_at=datetime.fromisoformat(data['sent_at']) if 'sent_at' in data else None,
            scheduled_at=datetime.fromisoformat(data['scheduled_at']) if 'scheduled_at' in data else None,
            tracking_enabled=bool(data.get('tracking_urls', True)),
            pre_header=data.get('pre_header'),
            stats=data.get('stats', {})
        )


@dataclass
class CampaignTotalInformation:
    """
    Represents total campaign information from Acumbamail API.
    
    Attributes:
        total_delivered (int): Total number of emails delivered
        soft_bounces (int): Number of soft bounces
        campaign_url (str): URL to view the campaign
        unsubscribes (int): Number of unsubscribes
        complaints (int): Number of complaints
        unique_clicks (int): Number of unique clicks
        unopened (int): Number of unopened emails
        emails_to_send (int): Total emails to be sent
        opened (int): Number of opened emails
        hard_bounces (int): Number of hard bounces
        total_clicks (int): Total number of clicks
    """
    total_delivered: int = 0
    soft_bounces: int = 0
    campaign_url: str = ""
    unsubscribes: int = 0
    complaints: int = 0
    unique_clicks: int = 0
    unopened: int = 0
    emails_to_send: int = 0
    opened: int = 0
    hard_bounces: int = 0
    total_clicks: int = 0

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'CampaignTotalInformation':
        """
        Create a CampaignTotalInformation instance from API response data.
        
        Args:
            data (Dict[str, Any]): Raw API response data
            
        Returns:
            CampaignTotalInformation: A new CampaignTotalInformation instance
        """
        return cls(
            total_delivered=int(data.get('total_delivered', 0)),
            soft_bounces=int(data.get('soft_bounces', 0)),
            campaign_url=str(data.get('campaign_url', '')),
            unsubscribes=int(data.get('unsubscribes', 0)),
            complaints=int(data.get('complaints', 0)),
            unique_clicks=int(data.get('unique_clicks', 0)),
            unopened=int(data.get('unopened', 0)),
            emails_to_send=int(data.get('emails_to_send', 0)),
            opened=int(data.get('opened', 0)),
            hard_bounces=int(data.get('hard_bounces', 0)),
            total_clicks=int(data.get('total_clicks', 0))
        )


@dataclass
class CampaignClick:
    """
    Represents a click event in a campaign.
    
    This class stores information about URL clicks in an email campaign, including
    both total clicks and unique clicks, along with their respective rates.
    
    Attributes:
        url (str): The URL that was clicked
        clicks (int): Total number of times the URL was clicked
        unique_clicks (int): Number of unique subscribers who clicked the URL
        click_rate (float): Percentage of total clicks vs total recipients
        unique_click_rate (float): Percentage of unique clicks vs total recipients
        
    Example:
        >>> data = {
        ...     'url': 'https://example.com',
        ...     'clicks': 100,
        ...     'unique_clicks': 80,
        ...     'click_rate': 0.15,
        ...     'unique_click_rate': 0.12
        ... }
        >>> click = CampaignClick.from_api(data)
        >>> click.url
        'https://example.com'
    """
    url: str
    clicks: int
    unique_clicks: int
    click_rate: float
    unique_click_rate: float

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'CampaignClick':
        """
        Create a CampaignClick instance from API response data.
        
        Args:
            data (Dict[str, Any]): Raw API response data containing click statistics
            
        Returns:
            CampaignClick: A new CampaignClick instance with parsed data
            
        Example:
            >>> data = {
            ...     'url': 'https://example.com',
            ...     'clicks': '100',
            ...     'unique_clicks': '80',
            ...     'click_rate': '0.15',
            ...     'unique_click_rate': '0.12'
            ... }
            >>> click = CampaignClick.from_api(data)
        """
        return cls(
            url=data['url'],
            clicks=int(data.get('clicks', 0)),
            unique_clicks=int(data.get('unique_clicks', 0)),
            click_rate=float(data.get('click_rate', 0)),
            unique_click_rate=float(data.get('unique_click_rate', 0))
        )

@dataclass
class CampaignOpener:
    """
    Represents an opener event in a campaign.
    
    This class stores detailed information about when and how a subscriber opened
    an email campaign, including technical details about their device and location.
    
    Attributes:
        email (str): Email address of the subscriber who opened the email
        opened_at (datetime): Timestamp when the email was opened
        ip (Optional[str]): IP address of the subscriber
        user_agent (Optional[str]): User agent string from the subscriber's browser
        country (Optional[str]): Country code where the email was opened
        browser (Optional[str]): Browser name used to open the email
        os (Optional[str]): Operating system of the device
        device (Optional[str]): Type of device used to open the email
        
    Example:
        >>> data = {
        ...     'email': 'user@example.com',
        ...     'opened_at': '2024-03-20T10:30:00Z',
        ...     'country': 'ES',
        ...     'browser': 'Chrome'
        ... }
        >>> opener = CampaignOpener.from_api(data)
        >>> opener.email
        'user@example.com'
    """
    email: str
    opened_at: datetime
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    country: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    device: Optional[str] = None

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'CampaignOpener':
        """
        Create a CampaignOpener instance from API response data.
        
        Args:
            data (Dict[str, Any]): Raw API response data containing opener information
            
        Returns:
            CampaignOpener: A new CampaignOpener instance with parsed data
            
        Example:
            >>> data = {
            ...     'email': 'user@example.com',
            ...     'opened_at': '2024-03-20T10:30:00Z',
            ...     'country': 'ES',
            ...     'browser': 'Chrome'
            ... }
            >>> opener = CampaignOpener.from_api(data)
        """
        return cls(
            email=data['email'],
            opened_at=datetime.fromisoformat(data['opened_at']),
            ip=data.get('ip'),
            user_agent=data.get('user_agent'),
            country=data.get('country'),
            browser=data.get('browser'),
            os=data.get('os'),
            device=data.get('device')
        )

@dataclass
class CampaignSoftBounce:
    """
    Represents a soft bounce event in a campaign.
    
    A soft bounce occurs when an email cannot be delivered temporarily, such as
    when the recipient's mailbox is full or the server is temporarily unavailable.
    
    Attributes:
        email (str): Email address that caused the bounce
        bounced_at (datetime): Timestamp when the bounce occurred
        reason (str): Description of why the bounce occurred
        status (str): Bounce status code or category
        diagnostic_code (Optional[str]): Technical details about the bounce
        
    Example:
        >>> data = {
        ...     'email': 'user@example.com',
        ...     'bounced_at': '2024-03-20T10:30:00Z',
        ...     'reason': 'Mailbox full',
        ...     'status': '4.2.2'
        ... }
        >>> bounce = CampaignSoftBounce.from_api(data)
        >>> bounce.email
        'user@example.com'
    """
    email: str
    bounced_at: datetime
    reason: str
    status: str
    diagnostic_code: Optional[str] = None

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'CampaignSoftBounce':
        """
        Create a CampaignSoftBounce instance from API response data.
        
        Args:
            data (Dict[str, Any]): Raw API response data containing bounce information
            
        Returns:
            CampaignSoftBounce: A new CampaignSoftBounce instance with parsed data
            
        Example:
            >>> data = {
            ...     'email': 'user@example.com',
            ...     'bounced_at': '2024-03-20T10:30:00Z',
            ...     'reason': 'Mailbox full',
            ...     'status': '4.2.2'
            ... }
            >>> bounce = CampaignSoftBounce.from_api(data)
        """
        return cls(
            email=data['email'],
            bounced_at=datetime.fromisoformat(data['bounced_at']),
            reason=data['reason'],
            status=data['status'],
            diagnostic_code=data.get('diagnostic_code')
        )

@dataclass
class Template:
    """
    Represents an email template in Acumbamail.
    
    Email templates are reusable HTML structures that can be used to create
    consistent-looking campaigns. They can include merge tags and other
    dynamic content.
    
    Attributes:
        id (int): Unique identifier of the template
        name (str): Name of the template
        content (str): HTML content of the template
        created_at (Optional[datetime]): When the template was created
        updated_at (Optional[datetime]): When the template was last modified
        
    Example:
        >>> data = {
        ...     'id': 123,
        ...     'name': 'Welcome Email',
        ...     'content': '<html><body>Welcome!</body></html>',
        ...     'created_at': '2024-03-20T10:30:00Z'
        ... }
        >>> template = Template.from_api(data)
        >>> template.name
        'Welcome Email'
    """
    id: int
    name: str
    content: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'Template':
        """
        Create a Template instance from API response data.
        
        Args:
            data (Dict[str, Any]): Raw API response data containing template information
            
        Returns:
            Template: A new Template instance with parsed data
            
        Example:
            >>> data = {
            ...     'id': 123,
            ...     'name': 'Welcome Email',
            ...     'content': '<html><body>Welcome!</body></html>',
            ...     'created_at': '2024-03-20T10:30:00Z'
            ... }
            >>> template = Template.from_api(data)
        """
        return cls(
            id=int(data['id']),
            name=data['name'],
            content=data['content'],
            created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if 'updated_at' in data else None
        )

__all__ = [
    "MailList", 
    "Subscriber", 
    "Campaign", 
    "CampaignClick", 
    "CampaignOpener", 
    "CampaignSoftBounce",
    "Template",
    "CampaignTotalInformation"
] 