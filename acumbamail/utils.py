"""
Utility functions for the Acumbamail SDK.
"""

import re
import json
import hashlib
from typing import Dict, Any, List, Union, Optional
from datetime import datetime

def validate_email(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email is valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def format_date(date: Union[str, datetime]) -> str:
    """
    Format date for API requests.
    
    Args:
        date: Date string or datetime object
        
    Returns:
        Formatted date string
    """
    if isinstance(date, str):
        try:
            date = datetime.fromisoformat(date.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError(f"Invalid date format: {date}")
    
    return date.strftime('%Y-%m-%d %H:%M:%S')

def generate_subscriber_hash(email: str, list_id: int) -> str:
    """
    Generate a unique hash for a subscriber.
    
    Args:
        email: Subscriber's email
        list_id: ID of the mailing list
        
    Returns:
        SHA-256 hash of email and list_id
    """
    data = f"{email.lower()}-{list_id}"
    return hashlib.sha256(data.encode()).hexdigest()

def clean_html(html: str) -> str:
    """
    Clean HTML content for email.
    
    Args:
        html: HTML content to clean
        
    Returns:
        Cleaned HTML content
    """
    # Remove multiple newlines
    html = re.sub(r'\n\s*\n', '\n', html)
    
    # Remove whitespace between tags
    html = re.sub(r'>\s+<', '><', html)
    
    # Remove comments
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    
    return html.strip()

def merge_subscriber_fields(
    default_fields: Dict[str, Any],
    custom_fields: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Merge default and custom subscriber fields.
    
    Args:
        default_fields: Default fields for all subscribers
        custom_fields: Custom fields for specific subscriber
        
    Returns:
        Merged fields dictionary
    """
    fields = default_fields.copy()
    
    if custom_fields:
        fields.update(custom_fields)
    
    return fields

def parse_api_response(response: str) -> Any:
    """
    Parse API response safely.
    
    Args:
        response: API response string
        
    Returns:
        Parsed response data
        
    Raises:
        ValueError: If response cannot be parsed
    """
    try:
        if not response:
            return None
            
        # Try to parse as JSON
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
            
        # Try to parse as integer
        try:
            return int(response)
        except ValueError:
            pass
            
        # Return as string if no other format matches
        return response.strip()
        
    except Exception as e:
        raise ValueError(f"Failed to parse API response: {str(e)}")

def format_campaign_content(
    content: str,
    unsubscribe_url: str = "*|UNSUBSCRIBE_URL|*",
    tracking_pixel: bool = True
) -> str:
    """
    Format campaign content with required elements.
    
    Args:
        content: Email content
        unsubscribe_url: URL for unsubscribe link
        tracking_pixel: Whether to add tracking pixel
        
    Returns:
        Formatted email content
    """
    # Clean content
    content = clean_html(content)
    
    # Add unsubscribe link if not present
    if unsubscribe_url not in content:
        unsubscribe_text = (
            '<div style="text-align: center; font-size: 12px; color: #666; margin-top: 20px;">'
            f'<a href="{unsubscribe_url}">Unsubscribe</a>'
            '</div>'
        )
        content = f"{content}\n{unsubscribe_text}"
    
    # Add tracking pixel if requested
    if tracking_pixel:
        pixel = '*|TRACKING_PIXEL|*'
        if pixel not in content:
            content = f"{content}\n{pixel}"
    
    return content

def validate_campaign_data(data: Dict[str, Any]) -> List[str]:
    """
    Validate campaign data before sending.
    
    Args:
        data: Campaign data dictionary
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    required_fields = ['name', 'subject', 'content', 'from_name', 'from_email', 'list_ids']
    
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
            continue
            
        value = data[field]
        
        if not value:
            errors.append(f"Field cannot be empty: {field}")
            
        elif field == 'from_email' and not validate_email(value):
            errors.append(f"Invalid email format: {field}")
            
        elif field == 'list_ids' and not isinstance(value, (list, tuple)):
            errors.append(f"Must be a list: {field}")
            
    return errors

def format_subscriber_data(
    email: str,
    fields: Optional[Dict[str, Any]] = None,
    validate: bool = True
) -> Dict[str, Any]:
    """
    Format subscriber data for API requests.
    
    Args:
        email: Subscriber's email
        fields: Additional fields
        validate: Whether to validate email
        
    Returns:
        Formatted subscriber data
        
    Raises:
        ValueError: If email is invalid
    """
    if validate and not validate_email(email):
        raise ValueError(f"Invalid email format: {email}")
        
    data = {
        "email": email.lower(),
        "fields": fields or {}
    }
    
    return data 