# Acumbamail SDK for Python

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI](https://img.shields.io/pypi/v/acumbamail)](https://pypi.org/project/acumbamail/)

A modern, feature-rich Python SDK for the [Acumbamail](https://acumbamail.com/?refered=243965) API. This library provides both synchronous and asynchronous clients for managing email campaigns, mailing lists, subscribers, and analytics.

# Table of Contents

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [Referral program](#referral-program)
- [Features](#features)
- [Quick Start](#quick-start)
  - [Installation](#installation)
  - [Basic Usage](#basic-usage)
- [Postman Collection](#postman-collection)
  - [Using the Postman Collection](#using-the-postman-collection)
- [Configuration](#configuration)
  - [Client Initialization](#client-initialization)
- [Basic Usage](#basic-usage-1)
  - [Mailing Lists](#mailing-lists)
  - [Subscribers](#subscribers)
  - [Campaigns](#campaigns)
  - [Single Emails](#single-emails)
- [Asynchronous Usage](#asynchronous-usage)
- [Analytics and Statistics](#analytics-and-statistics)
  - [Campaign Analytics](#campaign-analytics)
  - [Click Analysis](#click-analysis)
  - [Opener Analysis](#opener-analysis)
  - [Browser and OS Statistics](#browser-and-os-statistics)
- [Advanced Examples](#advanced-examples)
  - [Bulk Subscriber Management](#bulk-subscriber-management)
  - [Campaign Performance Monitoring](#campaign-performance-monitoring)
  - [Automated Newsletter System](#automated-newsletter-system)
  - [A/B Testing Framework](#ab-testing-framework)
- [API Reference](#api-reference)
  - [Client Classes](#client-classes)
    - [AcumbamailClient (Synchronous)](#acumbamailclient-synchronous)
    - [AsyncAcumbamailClient (Asynchronous)](#asyncacumbamailclient-asynchronous)
  - [Core Methods](#core-methods)
    - [List Management](#list-management)
    - [Subscriber Management](#subscriber-management)
    - [Campaign Management](#campaign-management)
    - [Analytics](#analytics)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Contributing](#contributing)
- [License](#license)
- [Support](#support)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Referral program

If you sign up using this link, you'll get 15% off.

[https://acumbamail.com/?refered=243965](https://acumbamail.com/?refered=243965)

## Features

- **Dual Client Support**: Both synchronous (`AcumbamailClient`) and asynchronous (`AsyncAcumbamailClient`) clients
- **Modern HTTP Client**: Built on `httpx` for better performance and HTTP/2 support
- **Type Hints**: Full type annotation support for better IDE integration
- **Comprehensive API Coverage**: All major Acumbamail API endpoints supported
- **Error Handling**: Robust exception handling with specific error types
- **Rate Limiting**: Built-in rate limit handling with exponential backoff
- **Data Models**: Structured data models for all API responses
- **Documentation**: Extensive docstrings and examples


## Quick Start

### Installation

```bash
pip install acumbamail
```

### Basic Usage

```python
from acumbamail import AcumbamailClient

# Initialize the client
client = AcumbamailClient(
    auth_token='your-api-token',
    default_sender_name='Your Company',
    default_sender_email='noreply@yourcompany.com'
)

# Create a mailing list
mailing_list = client.create_list(
    name="Newsletter Subscribers",
    description="Our monthly newsletter list"
)

# Add a subscriber
subscriber = client.add_subscriber(
    email="user@example.com",
    list_id=mailing_list.id,
    fields={"name": "John Doe", "company": "Acme Corp"}
)

# Create and send a campaign
campaign = client.create_campaign(
    name="Welcome Campaign",
    subject="Welcome to our newsletter!",
    content="<h1>Welcome!</h1><p>Thank you for subscribing.</p>",
    list_ids=[mailing_list.id]
)
```


## Postman Collection

For testing and exploring the API, you can use the included Postman collection:

- **Acumbamail.postman_collection.json**: Complete collection with all API endpoints pre-configured

The collection includes:
- **Campaigns**: All campaign-related endpoints (getCampaignBasicInformation, getCampaignClicks, getCampaignLinks, etc.)
- **Subscribers**: All subscriber and list management endpoints (getLists, getSubscribers, getListStats, etc.)

### Using the Postman Collection

1. Import the `Acumbamail.postman_collection.json` file into Postman
2. Set up your environment variables:
   - `token`: Your Acumbamail API token
   - `basepath`: `https://acumbamail.com/api/1/`
   - `campaign_id`: Your campaign ID (for campaign-specific endpoints)
   - `list_id`: Your list ID (for list-specific endpoints)
3. Start testing the API endpoints directly from Postman

## Configuration

### Client Initialization

```python
from acumbamail import AcumbamailClient

# Basic configuration
client = AcumbamailClient(auth_token='your-token')

# Full configuration (optional)
client = AcumbamailClient(
    auth_token='your-token',
    default_sender_name='Your Company',
    default_sender_email='noreply@yourcompany.com',
    sender_company='Your Company Inc.',
    sender_country='US'
)
```

## Basic Usage

### Mailing Lists

```python
# Get all lists
lists = client.get_lists()
for mail_list in lists:
    print(f"{mail_list.name}: {mail_list.subscribers_count} subscribers")

# Create a new list
new_list = client.create_list(
    name="Product Updates",
    description="List for product announcements"
)

# Get list statistics
stats = client.get_list_stats(new_list.id)
print(f"Total subscribers: {stats['total_subscribers']}")
```

### Subscribers

```python
# Add a subscriber
subscriber = client.add_subscriber(
    email="user@example.com",
    list_id=mailing_list.id,
    fields={
        "name": "John Doe",
        "company": "Acme Corp",
        "preferences": "weekly"
    }
)

# Get all subscribers
subscribers = client.get_subscribers(mailing_list.id)
for subscriber in subscribers:
    print(f"Email: {subscriber.email}")
    print(f"Fields: {subscriber.fields}")

# Remove a subscriber
client.delete_subscriber("user@example.com", mailing_list.id)
```

### Campaigns

```python
# Create a campaign
campaign = client.create_campaign(
    name="Monthly Newsletter",
    subject="This month's updates",
    content="""
    <h1>Monthly Newsletter</h1>
    <p>Here are the latest updates:</p>
    <ul>
        <li>New feature released</li>
        <li>Upcoming events</li>
        <li>Special offers</li>
    </ul>
    """,
    list_ids=[mailing_list.id],
    pre_header="Stay updated with our latest news"
)

# Schedule a campaign
from datetime import datetime, timedelta
scheduled_time = datetime.now() + timedelta(days=1)
scheduled_campaign = client.create_campaign(
    name="Scheduled Campaign",
    subject="Scheduled message",
    content="<p>This will be sent tomorrow</p>",
    list_ids=[mailing_list.id],
    scheduled_at=scheduled_time
)
```

### Single Emails

```python
# Send a single email
email_id = client.send_single_email(
    to_email="customer@example.com",
    subject="Order Confirmation",
    content="<h1>Thank you for your order!</h1><p>Order #12345</p>",
    category="order_confirmation"
)
```

## Asynchronous Usage

```python
import asyncio
from acumbamail import AsyncAcumbamailClient

async def main():
    # Using context manager (recommended)
    async with AsyncAcumbamailClient(
        auth_token='your-token',
        default_sender_name='Your Company',
        default_sender_email='noreply@yourcompany.com'
    ) as client:
        
        # Get lists
        lists = await client.get_lists()
        
        # Create campaign
        campaign = await client.create_campaign(
            name="Async Campaign",
            subject="Hello from async!",
            content="<p>This was sent asynchronously</p>",
            list_ids=[lists[0].id]
        )
        
        # Get campaign statistics
        stats = await client.get_campaign_total_information(campaign.id)
        print(f"Opened: {stats.opened}")

# Run the async function
asyncio.run(main())
```

## Analytics and Statistics

### Campaign Analytics

```python
# Get comprehensive campaign statistics
stats = client.get_campaign_total_information(campaign_id)

print(f"Total delivered: {stats.total_delivered}")
print(f"Opened: {stats.opened}")
print(f"Unique clicks: {stats.unique_clicks}")
print(f"Hard bounces: {stats.hard_bounces}")
print(f"Unsubscribes: {stats.unsubscribes}")

# Calculate rates
if stats.total_delivered > 0:
    open_rate = (stats.opened / stats.total_delivered) * 100
    click_rate = (stats.unique_clicks / stats.total_delivered) * 100
    print(f"Open rate: {open_rate:.2f}%")
    print(f"Click rate: {click_rate:.2f}%")
```

### Click Analysis

```python
# Get detailed click statistics
clicks = client.get_campaign_clicks(campaign_id)

for click in clicks:
    print(f"URL: {click.url}")
    print(f"Total clicks: {click.clicks}")
    print(f"Unique clicks: {click.unique_clicks}")
    print(f"Click rate: {click.click_rate:.2%}")
```

### Opener Analysis

```python
# Get information about who opened the campaign
openers = client.get_campaign_openers(campaign_id)

for opener in openers:
    print(f"Email: {opener.email}")
    print(f"Opened at: {opener.opened_at}")
    print(f"Country: {opener.country}")
    print(f"Browser: {opener.browser}")
    print(f"OS: {opener.os}")
```

### Browser and OS Statistics

```python
# Get statistics by browser
browser_stats = client.get_campaign_openers_by_browser(campaign_id)
for browser, count in browser_stats.items():
    print(f"{browser}: {count} opens")

# Get statistics by operating system
os_stats = client.get_campaign_openers_by_os(campaign_id)
for os_name, count in os_stats.items():
    print(f"{os_name}: {count} opens")
```

## Advanced Examples

### Bulk Subscriber Management

```python
# Add multiple subscribers efficiently
subscribers_data = [
    ("user1@example.com", {"name": "User One", "company": "Corp A"}),
    ("user2@example.com", {"name": "User Two", "company": "Corp B"}),
    ("user3@example.com", {"name": "User Three", "company": "Corp C"})
]

for email, fields in subscribers_data:
    try:
        subscriber = client.add_subscriber(
            email=email,
            list_id=mailing_list.id,
            fields=fields
        )
        print(f"Added: {subscriber.email}")
    except Exception as e:
        print(f"Failed to add {email}: {e}")
```

### Campaign Performance Monitoring

```python
def monitor_campaign_performance(campaign_id):
    """Monitor campaign performance and alert on issues."""
    stats = client.get_campaign_total_information(campaign_id)
    
    # Calculate key metrics
    if stats.total_delivered > 0:
        open_rate = (stats.opened / stats.total_delivered) * 100
        click_rate = (stats.unique_clicks / stats.total_delivered) * 100
        bounce_rate = (stats.hard_bounces / stats.total_delivered) * 100
        
        print(f"Campaign Performance:")
        print(f"  Open rate: {open_rate:.2f}%")
        print(f"  Click rate: {click_rate:.2f}%")
        print(f"  Bounce rate: {bounce_rate:.2f}%")
        
        # Alert on poor performance
        if open_rate < 15:
            print("⚠️  Warning: Low open rate detected")
        if bounce_rate > 5:
            print("⚠️  Warning: High bounce rate detected")
        if stats.complaints > 0:
            print("⚠️  Warning: Complaints detected")
```

### Automated Newsletter System

```python
from datetime import datetime, timedelta

def send_weekly_newsletter():
    """Send weekly newsletter to all active subscribers."""
    
    # Get the newsletter list
    lists = client.get_lists()
    newsletter_list = next((l for l in lists if "newsletter" in l.name.lower()), None)
    
    if not newsletter_list:
        print("Newsletter list not found")
        return
    
    # Create newsletter content
    content = """
    <h1>Weekly Newsletter</h1>
    <p>Here's what happened this week:</p>
    <ul>
        <li>New product features</li>
        <li>Upcoming events</li>
        <li>Community highlights</li>
    </ul>
    <p>Stay tuned for more updates!</p>
    """
    
    # Create and send campaign
    campaign = client.create_campaign(
        name=f"Weekly Newsletter - {datetime.now().strftime('%Y-%m-%d')}",
        subject="Your weekly update is here!",
        content=content,
        list_ids=[newsletter_list.id],
        pre_header="Your weekly dose of updates and insights"
    )
    
    print(f"Newsletter sent! Campaign ID: {campaign.id}")
```

### A/B Testing Framework

```python
def run_ab_test(subject_a, subject_b, content_a, content_b, list_id):
    """Run A/B test with two different subject lines and content."""
    
    # Create two campaigns
    campaign_a = client.create_campaign(
        name="A/B Test - Version A",
        subject=subject_a,
        content=content_a,
        list_ids=[list_id]
    )
    
    campaign_b = client.create_campaign(
        name="A/B Test - Version B",
        subject=subject_b,
        content=content_b,
        list_ids=[list_id]
    )
    
    print(f"Created A/B test campaigns:")
    print(f"  Version A: {campaign_a.id}")
    print(f"  Version B: {campaign_b.id}")
    
    return campaign_a.id, campaign_b.id

def analyze_ab_test(campaign_a_id, campaign_b_id):
    """Analyze A/B test results."""
    
    stats_a = client.get_campaign_total_information(campaign_a_id)
    stats_b = client.get_campaign_total_information(campaign_b_id)
    
    # Calculate performance metrics
    open_rate_a = (stats_a.opened / stats_a.total_delivered) * 100 if stats_a.total_delivered > 0 else 0
    open_rate_b = (stats_b.opened / stats_b.total_delivered) * 100 if stats_b.total_delivered > 0 else 0
    
    click_rate_a = (stats_a.unique_clicks / stats_a.total_delivered) * 100 if stats_a.total_delivered > 0 else 0
    click_rate_b = (stats_b.unique_clicks / stats_b.total_delivered) * 100 if stats_b.total_delivered > 0 else 0
    
    print("A/B Test Results:")
    print(f"Version A - Open rate: {open_rate_a:.2f}%, Click rate: {click_rate_a:.2f}%")
    print(f"Version B - Open rate: {open_rate_b:.2f}%, Click rate: {click_rate_b:.2f}%")
    
    # Determine winner
    if open_rate_b > open_rate_a:
        print("🎉 Version B wins for open rate!")
    elif open_rate_a > open_rate_b:
        print("🎉 Version A wins for open rate!")
    else:
        print("🤝 Tie for open rate")
```

## API Reference

### Client Classes

#### AcumbamailClient (Synchronous)

```python
class AcumbamailClient:
    def __init__(
        self,
        auth_token: str,
        default_sender_name: str = None,
        default_sender_email: str = None,
        *,
        sender_company: str = None,
        sender_country: str = None
    )
```

#### AsyncAcumbamailClient (Asynchronous)

```python
class AsyncAcumbamailClient:
    def __init__(
        self,
        auth_token: str,
        default_sender_name: str = None,
        default_sender_email: str = None,
        *,
        sender_company: str = None,
        sender_country: str = None,
        timeout: float = 30.0
    )
```

### Core Methods

#### List Management

- `get_lists()` - Retrieve all mailing lists
- `create_list(name, description)` - Create a new mailing list
- `get_list_stats(list_id)` - Get list statistics
- `get_list_fields(list_id)` - Get custom fields
- `get_list_segments(list_id)` - Get list segments

#### Subscriber Management

- `get_subscribers(list_id)` - Get all subscribers
- `add_subscriber(email, list_id, fields)` - Add a subscriber
- `delete_subscriber(email, list_id)` - Remove a subscriber

#### Campaign Management

- `create_campaign(name, subject, content, list_ids, ...)` - Create a campaign
- `get_campaigns(complete_json)` - Get all campaigns
- `send_single_email(to_email, subject, content, ...)` - Send single email

#### Analytics

- `get_campaign_total_information(campaign_id)` - Get comprehensive stats
- `get_campaign_clicks(campaign_id)` - Get click statistics
- `get_campaign_openers(campaign_id)` - Get opener information
- `get_campaign_soft_bounces(campaign_id)` - Get bounce information

## Error Handling

The SDK provides specific exception types for different error scenarios:

```python
from acumbamail import (
    AcumbamailError,
    AcumbamailRateLimitError,
    AcumbamailAPIError,
    AcumbamailValidationError
)

try:
    campaign = client.create_campaign(
        name="Test Campaign",
        subject="Hello",
        content="<p>Test</p>",
        list_ids=[123]
    )
except AcumbamailValidationError as e:
    print(f"Validation error: {e}")
except AcumbamailRateLimitError as e:
    print(f"Rate limit exceeded: {e}")
except AcumbamailAPIError as e:
    print(f"API error: {e}")
except AcumbamailError as e:
    print(f"General error: {e}")
```

## Examples

You can find examples in the [examples](examples) directory.

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

I don't offer support for this project apart from the free time I can dedicate to it. If you find a bug, please report it in the [GitHub Issues](https://github.com/cr0hn/py-acumbamail/issues) section.

[GitHub Issues](https://github.com/cr0hn/py-acumbamail/issues)

> [!NOTE] If you need commercial support for this project, please contact me at [cr0hn<-at->cr0hn.com](mailto:cr0hn<-at->cr0hn.com).