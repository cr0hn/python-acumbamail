#!/usr/bin/env python3
"""
Bulk Operations Example

This example demonstrates how to perform bulk operations with the Acumbamail SDK,
including adding multiple subscribers, creating multiple campaigns, and batch processing.
"""

import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
from acumbamail import AcumbamailClient

def bulk_add_subscribers(client, list_id: int, subscribers_data: List[Dict[str, Any]]):
    """Add multiple subscribers to a list with error handling."""
    
    print(f"📧 Adding {len(subscribers_data)} subscribers to list {list_id}")
    print("=" * 60)
    
    successful = 0
    failed = 0
    errors = []
    
    for i, subscriber_data in enumerate(subscribers_data, 1):
        try:
            subscriber = client.add_subscriber(
                email=subscriber_data['email'],
                list_id=list_id,
                fields=subscriber_data.get('fields', {})
            )
            print(f"✅ {i:3d}. Added: {subscriber.email}")
            successful += 1
            
            # Small delay to avoid rate limiting
            time.sleep(0.1)
            
        except Exception as e:
            print(f"❌ {i:3d}. Failed: {subscriber_data['email']} - {str(e)}")
            failed += 1
            errors.append({
                'email': subscriber_data['email'],
                'error': str(e)
            })
    
    print(f"\n📊 Bulk Add Results:")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(successful / len(subscribers_data) * 100):.1f}%")
    
    if errors:
        print(f"\n❌ Errors encountered:")
        for error in errors[:5]:  # Show first 5 errors
            print(f"  - {error['email']}: {error['error']}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more errors")
    
    return successful, failed, errors

def bulk_create_campaigns(client, campaigns_data: List[Dict[str, Any]]):
    """Create multiple campaigns with different configurations."""
    
    print(f"📢 Creating {len(campaigns_data)} campaigns")
    print("=" * 60)
    
    created_campaigns = []
    failed_campaigns = []
    
    for i, campaign_data in enumerate(campaigns_data, 1):
        try:
            campaign = client.create_campaign(
                name=campaign_data['name'],
                subject=campaign_data['subject'],
                content=campaign_data['content'],
                list_ids=campaign_data['list_ids'],
                pre_header=campaign_data.get('pre_header'),
                scheduled_at=campaign_data.get('scheduled_at')
            )
            print(f"✅ {i:2d}. Created: {campaign.name} (ID: {campaign.id})")
            created_campaigns.append(campaign)
            
        except Exception as e:
            print(f"❌ {i:2d}. Failed: {campaign_data['name']} - {str(e)}")
            failed_campaigns.append({
                'name': campaign_data['name'],
                'error': str(e)
            })
    
    print(f"\n📊 Bulk Campaign Creation Results:")
    print(f"✅ Created: {len(created_campaigns)}")
    print(f"❌ Failed: {len(failed_campaigns)}")
    
    return created_campaigns, failed_campaigns

def bulk_send_single_emails(client, emails_data: List[Dict[str, Any]]):
    """Send multiple single emails."""
    
    print(f"📤 Sending {len(emails_data)} single emails")
    print("=" * 60)
    
    successful = 0
    failed = 0
    email_ids = []
    
    for i, email_data in enumerate(emails_data, 1):
        try:
            email_id = client.send_single_email(
                to_email=email_data['to_email'],
                subject=email_data['subject'],
                content=email_data['content'],
                category=email_data.get('category', 'bulk_send')
            )
            print(f"✅ {i:3d}. Sent to: {email_data['to_email']} (ID: {email_id})")
            successful += 1
            email_ids.append(email_id)
            
            # Small delay to avoid rate limiting
            time.sleep(0.2)
            
        except Exception as e:
            print(f"❌ {i:3d}. Failed: {email_data['to_email']} - {str(e)}")
            failed += 1
    
    print(f"\n📊 Bulk Single Email Results:")
    print(f"✅ Sent: {successful}")
    print(f"❌ Failed: {failed}")
    
    return successful, failed, email_ids

def generate_sample_subscribers(count: int = 100) -> List[Dict[str, Any]]:
    """Generate sample subscriber data for testing."""
    
    subscribers = []
    companies = ["Acme Corp", "Tech Solutions", "Global Industries", "Startup Inc", "Enterprise Ltd"]
    departments = ["Engineering", "Marketing", "Sales", "HR", "Finance", "Operations"]
    
    for i in range(count):
        subscriber = {
            'email': f"user{i+1}@example.com",
            'fields': {
                'name': f"User {i+1}",
                'company': companies[i % len(companies)],
                'department': departments[i % len(departments)],
                'employee_id': f"EMP{i+1:04d}",
                'location': "Remote" if i % 3 == 0 else "Office",
                'subscription_date': datetime.now().strftime('%Y-%m-%d')
            }
        }
        subscribers.append(subscriber)
    
    return subscribers

def generate_sample_campaigns(list_ids: List[int]) -> List[Dict[str, Any]]:
    """Generate sample campaign data for testing."""
    
    campaigns = []
    
    # Welcome series
    campaigns.append({
        'name': 'Welcome Series - Day 1',
        'subject': 'Welcome to our community!',
        'content': '''
        <h1>Welcome!</h1>
        <p>Thank you for joining our community. We're excited to have you on board!</p>
        <p>In the next few days, we'll send you some helpful resources to get started.</p>
        ''',
        'list_ids': list_ids,
        'pre_header': 'Welcome to our community!'
    })
    
    campaigns.append({
        'name': 'Welcome Series - Day 3',
        'subject': 'Getting started with our platform',
        'content': '''
        <h1>Getting Started</h1>
        <p>Now that you're part of our community, let's get you started with our platform.</p>
        <p>Here are some key features you should know about:</p>
        <ul>
            <li>Feature 1: Description</li>
            <li>Feature 2: Description</li>
            <li>Feature 3: Description</li>
        </ul>
        ''',
        'list_ids': list_ids,
        'pre_header': 'Learn how to get the most out of our platform'
    })
    
    # Product updates
    campaigns.append({
        'name': 'Product Update - New Features',
        'subject': 'New features just released!',
        'content': '''
        <h1>New Features Released</h1>
        <p>We've just released some exciting new features that we think you'll love!</p>
        <h2>What's New:</h2>
        <ul>
            <li>Enhanced dashboard</li>
            <li>Improved analytics</li>
            <li>Better mobile experience</li>
        </ul>
        <p>Try them out and let us know what you think!</p>
        ''',
        'list_ids': list_ids,
        'pre_header': 'Check out our latest features'
    })
    
    # Newsletter
    campaigns.append({
        'name': 'Monthly Newsletter - March 2024',
        'subject': 'March Newsletter: Industry insights and updates',
        'content': '''
        <h1>March Newsletter</h1>
        <p>Here's what's happening in our industry this month:</p>
        <h2>Industry Insights</h2>
        <p>Latest trends and developments...</p>
        <h2>Company Updates</h2>
        <p>What we've been working on...</p>
        <h2>Upcoming Events</h2>
        <p>Don't miss these important dates...</p>
        ''',
        'list_ids': list_ids,
        'pre_header': 'Stay updated with industry insights and company news'
    })
    
    return campaigns

def generate_sample_single_emails() -> List[Dict[str, Any]]:
    """Generate sample single email data for testing."""
    
    emails = []
    
    # Order confirmations
    for i in range(5):
        emails.append({
            'to_email': f"customer{i+1}@example.com",
            'subject': f'Order Confirmation - Order #{1000+i}',
            'content': f'''
            <h1>Order Confirmation</h1>
            <p>Thank you for your order!</p>
            <p><strong>Order Number:</strong> #{1000+i}</p>
            <p><strong>Order Date:</strong> {datetime.now().strftime('%Y-%m-%d')}</p>
            <p>We'll send you a tracking number once your order ships.</p>
            ''',
            'category': 'order_confirmation'
        })
    
    # Support responses
    for i in range(3):
        emails.append({
            'to_email': f"support{i+1}@example.com",
            'subject': 'Your support ticket has been updated',
            'content': f'''
            <h1>Support Ticket Update</h1>
            <p>Your support ticket has been updated.</p>
            <p><strong>Ticket ID:</strong> SUP-{2024}{i+1:03d}</p>
            <p>Our team is working on resolving your issue. We'll keep you updated.</p>
            ''',
            'category': 'support'
        })
    
    # Personal invitations
    for i in range(2):
        emails.append({
            'to_email': f"invite{i+1}@example.com",
            'subject': 'Exclusive invitation: Join our beta program',
            'content': f'''
            <h1>Exclusive Beta Invitation</h1>
            <p>You've been selected to join our exclusive beta program!</p>
            <p>As a beta tester, you'll get early access to new features and help shape our product.</p>
            <p>Click here to join: <a href="https://example.com/beta">Join Beta</a></p>
            ''',
            'category': 'invitation'
        })
    
    return emails

def main():
    """Main function to demonstrate bulk operations."""
    
    # Initialize client
    client = AcumbamailClient(
        auth_token=os.getenv("ACUMBAMAIL_AUTH_TOKEN"),
        default_sender_name="Bulk Operations Example",
        default_sender_email="bulk@example.com"
    )
    
    try:
        print("🚀 Bulk Operations Example")
        print("=" * 60)
        
        # Get or create a test list
        print("📋 Setting up test list...")
        lists = client.get_lists()
        
        if not lists:
            print("Creating a new test list...")
            test_list = client.create_list(
                name="Bulk Operations Test List",
                description="List for testing bulk operations"
            )
        else:
            test_list = lists[0]  # Use the first available list
            print(f"Using existing list: {test_list.name}")
        
        print(f"✅ Using list: {test_list.name} (ID: {test_list.id})")
        
        # 1. Bulk add subscribers
        print(f"\n{'='*60}")
        print("1. BULK SUBSCRIBER ADDITION")
        print("=" * 60)
        
        sample_subscribers = generate_sample_subscribers(20)  # Reduced for demo
        successful, failed, errors = bulk_add_subscribers(client, test_list.id, sample_subscribers)
        
        # 2. Bulk create campaigns
        print(f"\n{'='*60}")
        print("2. BULK CAMPAIGN CREATION")
        print("=" * 60)
        
        sample_campaigns = generate_sample_campaigns([test_list.id])
        created_campaigns, failed_campaigns = bulk_create_campaigns(client, sample_campaigns)
        
        # 3. Bulk send single emails
        print(f"\n{'='*60}")
        print("3. BULK SINGLE EMAIL SENDING")
        print("=" * 60)
        
        sample_emails = generate_sample_single_emails()
        sent, failed_emails, email_ids = bulk_send_single_emails(client, sample_emails)
        
        # Summary
        print(f"\n{'='*60}")
        print("📊 BULK OPERATIONS SUMMARY")
        print("=" * 60)
        print(f"✅ Subscribers added: {successful}")
        print(f"✅ Campaigns created: {len(created_campaigns)}")
        print(f"✅ Single emails sent: {sent}")
        print(f"❌ Total failures: {failed + len(failed_campaigns) + failed_emails}")
        
        if created_campaigns:
            print(f"\n📢 Created Campaigns:")
            for campaign in created_campaigns:
                print(f"  - {campaign.name} (ID: {campaign.id})")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 