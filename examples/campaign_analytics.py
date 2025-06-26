#!/usr/bin/env python3
"""
Campaign Analytics Example

This example demonstrates how to analyze campaign performance,
generate reports, and track key metrics over time.
"""

import os
from datetime import datetime, timedelta
from acumbamail import AcumbamailClient

def analyze_campaign_performance(client, campaign_id):
    """Analyze a single campaign's performance."""
    
    print(f"📊 Analyzing Campaign ID: {campaign_id}")
    print("=" * 50)
    
    # Get comprehensive campaign statistics
    stats = client.get_campaign_total_information(campaign_id)
    
    # Calculate key metrics
    total_sent = stats.total_delivered
    if total_sent > 0:
        open_rate = (stats.opened / total_sent) * 100
        click_rate = (stats.unique_clicks / total_sent) * 100
        bounce_rate = (stats.hard_bounces / total_sent) * 100
        unsubscribe_rate = (stats.unsubscribes / total_sent) * 100
    else:
        open_rate = click_rate = bounce_rate = unsubscribe_rate = 0
    
    # Display basic metrics
    print(f"📧 Total Delivered: {total_sent:,}")
    print(f"👁️  Opened: {stats.opened:,} ({open_rate:.2f}%)")
    print(f"🖱️  Unique Clicks: {stats.unique_clicks:,} ({click_rate:.2f}%)")
    print(f"📤 Total Clicks: {stats.total_clicks:,}")
    print(f"❌ Hard Bounces: {stats.hard_bounces:,} ({bounce_rate:.2f}%)")
    print(f"📭 Unsubscribes: {stats.unsubscribes:,} ({unsubscribe_rate:.2f}%)")
    print(f"🚫 Complaints: {stats.complaints:,}")
    
    # Performance assessment
    print("\n🎯 Performance Assessment:")
    if open_rate >= 25:
        print("✅ Excellent open rate!")
    elif open_rate >= 15:
        print("👍 Good open rate")
    elif open_rate >= 10:
        print("⚠️  Average open rate")
    else:
        print("❌ Low open rate - consider improving subject lines")
    
    if click_rate >= 3:
        print("✅ Excellent click rate!")
    elif click_rate >= 1:
        print("👍 Good click rate")
    else:
        print("⚠️  Low click rate - consider improving content")
    
    if bounce_rate <= 2:
        print("✅ Excellent bounce rate!")
    elif bounce_rate <= 5:
        print("👍 Good bounce rate")
    else:
        print("❌ High bounce rate - clean your list")
    
    return stats

def analyze_clicks(client, campaign_id):
    """Analyze click performance for a campaign."""
    
    print(f"\n🔗 Click Analysis for Campaign ID: {campaign_id}")
    print("=" * 50)
    
    clicks = client.get_campaign_clicks(campaign_id)
    
    if not clicks:
        print("No clicks recorded for this campaign.")
        return
    
    # Sort by total clicks
    clicks_sorted = sorted(clicks, key=lambda x: x.clicks, reverse=True)
    
    print(f"Total URLs with clicks: {len(clicks)}")
    print("\nTop performing URLs:")
    
    for i, click in enumerate(clicks_sorted[:5], 1):
        print(f"{i}. {click.url}")
        print(f"   Total clicks: {click.clicks:,}")
        print(f"   Unique clicks: {click.unique_clicks:,}")
        print(f"   Click rate: {click.click_rate:.2%}")
        print()

def analyze_openers(client, campaign_id):
    """Analyze who opened the campaign."""
    
    print(f"\n👥 Opener Analysis for Campaign ID: {campaign_id}")
    print("=" * 50)
    
    openers = client.get_campaign_openers(campaign_id)
    
    if not openers:
        print("No opens recorded for this campaign.")
        return
    
    print(f"Total unique opens: {len(openers)}")
    
    # Analyze by country
    countries = {}
    browsers = {}
    operating_systems = {}
    
    for opener in openers:
        # Country analysis
        country = opener.country or "Unknown"
        countries[country] = countries.get(country, 0) + 1
        
        # Browser analysis
        browser = opener.browser or "Unknown"
        browsers[browser] = browsers.get(browser, 0) + 1
        
        # OS analysis
        os_name = opener.os or "Unknown"
        operating_systems[os_name] = operating_systems.get(os_name, 0) + 1
    
    # Display top countries
    print("\n🌍 Top Countries:")
    for country, count in sorted(countries.items(), key=lambda x: x[1], reverse=True)[:5]:
        percentage = (count / len(openers)) * 100
        print(f"  {country}: {count} ({percentage:.1f}%)")
    
    # Display top browsers
    print("\n🌐 Top Browsers:")
    for browser, count in sorted(browsers.items(), key=lambda x: x[1], reverse=True)[:5]:
        percentage = (count / len(openers)) * 100
        print(f"  {browser}: {count} ({percentage:.1f}%)")
    
    # Display top operating systems
    print("\n💻 Top Operating Systems:")
    for os_name, count in sorted(operating_systems.items(), key=lambda x: x[1], reverse=True)[:5]:
        percentage = (count / len(openers)) * 100
        print(f"  {os_name}: {count} ({percentage:.1f}%)")

def analyze_bounces(client, campaign_id):
    """Analyze bounce information for a campaign."""
    
    print(f"\n📤 Bounce Analysis for Campaign ID: {campaign_id}")
    print("=" * 50)
    
    bounces = client.get_campaign_soft_bounces(campaign_id)
    
    if not bounces:
        print("No bounces recorded for this campaign.")
        return
    
    print(f"Total soft bounces: {len(bounces)}")
    
    # Analyze bounce reasons
    bounce_reasons = {}
    for bounce in bounces:
        reason = bounce.reason or "Unknown"
        bounce_reasons[reason] = bounce_reasons.get(reason, 0) + 1
    
    print("\n📋 Bounce Reasons:")
    for reason, count in sorted(bounce_reasons.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(bounces)) * 100
        print(f"  {reason}: {count} ({percentage:.1f}%)")

def generate_campaign_report(client, campaign_id):
    """Generate a comprehensive campaign report."""
    
    print(f"\n📋 CAMPAIGN REPORT")
    print("=" * 60)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Campaign ID: {campaign_id}")
    print("=" * 60)
    
    # Get campaign basic info
    campaigns = client.get_campaigns(complete_json=True)
    campaign = next((c for c in campaigns if c.id == campaign_id), None)
    
    if campaign:
        print(f"Campaign Name: {campaign.name}")
        print(f"Subject: {campaign.subject}")
        print(f"Sent Date: {campaign.sent_at}")
        print()
    
    # Run all analyses
    stats = analyze_campaign_performance(client, campaign_id)
    analyze_clicks(client, campaign_id)
    analyze_openers(client, campaign_id)
    analyze_bounces(client, campaign_id)
    
    # Summary
    print(f"\n📊 SUMMARY")
    print("=" * 30)
    print(f"Campaign ID: {campaign_id}")
    print(f"Total Delivered: {stats.total_delivered:,}")
    print(f"Open Rate: {(stats.opened / stats.total_delivered * 100):.2f}%" if stats.total_delivered > 0 else "Open Rate: N/A")
    print(f"Click Rate: {(stats.unique_clicks / stats.total_delivered * 100):.2f}%" if stats.total_delivered > 0 else "Click Rate: N/A")
    print(f"Bounce Rate: {(stats.hard_bounces / stats.total_delivered * 100):.2f}%" if stats.total_delivered > 0 else "Bounce Rate: N/A")

def main():
    """Main function to run campaign analytics."""
    
    # Initialize client
    client = AcumbamailClient(
        auth_token=os.getenv("ACUMBAMAIL_AUTH_TOKEN"),
        default_sender_name="Analytics Example",
        default_sender_email="analytics@example.com"
    )
    
    try:
        # Get recent campaigns
        print("📋 Getting recent campaigns...")
        campaigns = client.get_campaigns(complete_json=True)
        
        if not campaigns:
            print("No campaigns found. Please create a campaign first.")
            return
        
        # Show available campaigns
        print(f"Found {len(campaigns)} campaigns:")
        for i, campaign in enumerate(campaigns[:5], 1):
            print(f"{i}. {campaign.name} (ID: {campaign.id})")
        
        # Analyze the most recent campaign
        if campaigns:
            latest_campaign = campaigns[0]
            print(f"\n🎯 Analyzing latest campaign: {latest_campaign.name}")
            generate_campaign_report(client, latest_campaign.id)
        
        # You can also analyze specific campaigns by ID
        # generate_campaign_report(client, 12345)  # Replace with actual campaign ID
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 