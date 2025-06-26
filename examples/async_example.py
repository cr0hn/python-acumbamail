#!/usr/bin/env python3
"""
Example usage of the asynchronous Acumbamail client.

This example demonstrates how to use the AsyncAcumbamailClient with asyncio and httpx.
"""

import asyncio
import os
from acumbamail import AsyncAcumbamailClient

async def main():
    # Initialize the async client using context manager
    async with AsyncAcumbamailClient(
        auth_token=os.getenv("ACUMBAMAIL_AUTH_TOKEN"),
        default_sender_name="John Doe",
        default_sender_email="john@example.com"
    ) as client:
        
        try:
            # Get all lists
            print("Fetching mailing lists...")
            lists = await client.get_lists()
            print(f"Found {len(lists)} lists")
            
            for mail_list in lists:
                print(f"- {mail_list.name} (ID: {mail_list.id})")
            
            # Create a new list
            print("\nCreating a new list...")
            new_list = await client.create_list(
                name="Async Test List",
                description="A test mailing list created with async client"
            )
            print(f"Created list: {new_list.name} (ID: {new_list.id})")
            
            # Add a subscriber
            print("\nAdding a subscriber...")
            subscriber = await client.add_subscriber(
                email="async-test@example.com",
                list_id=new_list.id,
                fields={"name": "Async Test User"}
            )
            print(f"Added subscriber: {subscriber.email}")
            
            # Get subscribers
            print("\nFetching subscribers...")
            subscribers = await client.get_subscribers(new_list.id)
            print(f"Found {len(subscribers)} subscribers")
            
            # Create a campaign
            print("\nCreating a campaign...")
            campaign = await client.create_campaign(
                name="Async Test Campaign",
                subject="Hello from Async Acumbamail!",
                content="<h1>Hello!</h1><p>This is a test email sent with async client.</p>",
                list_ids=[new_list.id],
                pre_header="Test email from Async Acumbamail SDK"
            )
            print(f"Created campaign: {campaign.name} (ID: {campaign.id})")
            
            # Send a single email
            print("\nSending a single email...")
            email_id = await client.send_single_email(
                to_email="async-test@example.com",
                subject="Async Single Test Email",
                content="<h1>Async Single Email Test</h1><p>This is a single email test with async client.</p>"
            )
            print(f"Sent email with ID: {email_id}")
            
            # Get campaign statistics
            print("\nFetching campaign statistics...")
            campaign_stats = await client.get_campaign_total_information(campaign.id)
            print(f"Campaign stats: {campaign_stats}")
            
        except Exception as e:
            print(f"Error: {e}")

async def alternative_usage():
    """
    Alternative way to use the async client without context manager.
    """
    client = AsyncAcumbamailClient(
        auth_token=os.getenv("ACUMBAMAIL_AUTH_TOKEN"),
        default_sender_name="John Doe",
        default_sender_email="john@example.com"
    )
    
    try:
        # Get templates
        print("Fetching templates...")
        templates = await client.get_templates()
        print(f"Found {len(templates)} templates")
        
        for template in templates:
            print(f"- {template.name} (ID: {template.id})")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Always close the client
        await client.close()

if __name__ == "__main__":
    # Run the main example
    asyncio.run(main())
    
    # Run the alternative example
    print("\n" + "="*50)
    print("Alternative usage example:")
    asyncio.run(alternative_usage()) 