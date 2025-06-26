#!/usr/bin/env python3
"""
Example usage of the synchronous Acumbamail client.

This example demonstrates how to use the AcumbamailClient with httpx.
"""

import os
from acumbamail import AcumbamailClient

def main():
    # Initialize the client
    client = AcumbamailClient(
        auth_token=os.getenv("ACUMBAMAIL_AUTH_TOKEN"),
        default_sender_name="John Doe",
        default_sender_email="john@example.com"
    )
    
    try:
        # Get all lists
        print("Fetching mailing lists...")
        lists = client.get_lists()
        print(f"Found {len(lists)} lists")
        
        for mail_list in lists:
            print(f"- {mail_list.name} (ID: {mail_list.id})")
        
        # Create a new list
        print("\nCreating a new list...")
        new_list = client.create_list(
            name="Test List",
            description="A test mailing list"
        )
        print(f"Created list: {new_list.name} (ID: {new_list.id})")
        
        # Add a subscriber
        print("\nAdding a subscriber...")
        subscriber = client.add_subscriber(
            email="test@example.com",
            list_id=new_list.id,
            fields={"name": "Test User"}
        )
        print(f"Added subscriber: {subscriber.email}")
        
        # Get subscribers
        print("\nFetching subscribers...")
        subscribers = client.get_subscribers(new_list.id)
        print(f"Found {len(subscribers)} subscribers")
        
        # Create a campaign
        print("\nCreating a campaign...")
        campaign = client.create_campaign(
            name="Test Campaign",
            subject="Hello from Acumbamail!",
            content="<h1>Hello!</h1><p>This is a test email.</p>",
            list_ids=[new_list.id],
            pre_header="Test email from Acumbamail SDK"
        )
        print(f"Created campaign: {campaign.name} (ID: {campaign.id})")
        
        # Send a single email
        print("\nSending a single email...")
        email_id = client.send_single_email(
            to_email="test@example.com",
            subject="Single Test Email",
            content="<h1>Single Email Test</h1><p>This is a single email test.</p>"
        )
        print(f"Sent email with ID: {email_id}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 