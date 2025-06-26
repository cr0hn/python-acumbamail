#!/usr/bin/env python3
"""
A/B Testing Example

This example demonstrates how to implement A/B testing for email campaigns,
including creating test variants, analyzing results, and determining winners.
"""

import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from acumbamail import AcumbamailClient

class ABTest:
    """A/B Testing framework for email campaigns."""
    
    def __init__(self, client: AcumbamailClient, test_name: str, list_id: int):
        self.client = client
        self.test_name = test_name
        self.list_id = list_id
        self.variants = []
        self.results = {}
    
    def add_variant(self, name: str, subject: str, content: str, pre_header: str = None):
        """Add a test variant."""
        self.variants.append({
            'name': name,
            'subject': subject,
            'content': content,
            'pre_header': pre_header
        })
    
    def create_test_campaigns(self) -> List[Dict[str, Any]]:
        """Create campaigns for all variants."""
        
        print(f"🧪 Creating A/B test campaigns for: {self.test_name}")
        print("=" * 60)
        
        created_campaigns = []
        
        for i, variant in enumerate(self.variants, 1):
            try:
                campaign = self.client.create_campaign(
                    name=f"{self.test_name} - {variant['name']}",
                    subject=variant['subject'],
                    content=variant['content'],
                    list_ids=[self.list_id],
                    pre_header=variant.get('pre_header')
                )
                
                print(f"✅ Variant {i}: {variant['name']} (Campaign ID: {campaign.id})")
                created_campaigns.append({
                    'variant': variant['name'],
                    'campaign_id': campaign.id,
                    'campaign': campaign
                })
                
            except Exception as e:
                print(f"❌ Failed to create variant {i}: {variant['name']} - {str(e)}")
        
        return created_campaigns
    
    def wait_for_results(self, wait_hours: int = 24):
        """Wait for campaign results to accumulate."""
        
        print(f"\n⏳ Waiting {wait_hours} hours for results to accumulate...")
        print("Note: In a real scenario, you would wait for actual time to pass.")
        print("For this example, we'll simulate waiting...")
        
        # In a real scenario, you would use: time.sleep(wait_hours * 3600)
        # For demo purposes, we'll just wait a few seconds
        time.sleep(3)
        print("✅ Results collection period completed!")
    
    def analyze_variant(self, campaign_id: int) -> Dict[str, Any]:
        """Analyze results for a single variant."""
        
        try:
            stats = self.client.get_campaign_total_information(campaign_id)
            
            # Calculate key metrics
            total_delivered = stats.total_delivered
            if total_delivered > 0:
                open_rate = (stats.opened / total_delivered) * 100
                click_rate = (stats.unique_clicks / total_delivered) * 100
                bounce_rate = (stats.hard_bounces / total_delivered) * 100
                unsubscribe_rate = (stats.unsubscribes / total_delivered) * 100
            else:
                open_rate = click_rate = bounce_rate = unsubscribe_rate = 0
            
            return {
                'campaign_id': campaign_id,
                'total_delivered': total_delivered,
                'opened': stats.opened,
                'unique_clicks': stats.unique_clicks,
                'total_clicks': stats.total_clicks,
                'hard_bounces': stats.hard_bounces,
                'unsubscribes': stats.unsubscribes,
                'complaints': stats.complaints,
                'open_rate': open_rate,
                'click_rate': click_rate,
                'bounce_rate': bounce_rate,
                'unsubscribe_rate': unsubscribe_rate
            }
            
        except Exception as e:
            print(f"❌ Error analyzing campaign {campaign_id}: {str(e)}")
            return None
    
    def analyze_all_variants(self, campaigns: List[Dict[str, Any]]):
        """Analyze results for all variants."""
        
        print(f"\n📊 Analyzing A/B test results for: {self.test_name}")
        print("=" * 60)
        
        results = {}
        
        for campaign_data in campaigns:
            variant_name = campaign_data['variant']
            campaign_id = campaign_data['campaign_id']
            
            print(f"\n🔍 Analyzing variant: {variant_name}")
            analysis = self.analyze_variant(campaign_id)
            
            if analysis:
                results[variant_name] = analysis
                print(f"  📧 Delivered: {analysis['total_delivered']:,}")
                print(f"  👁️  Open Rate: {analysis['open_rate']:.2f}%")
                print(f"  🖱️  Click Rate: {analysis['click_rate']:.2f}%")
                print(f"  ❌ Bounce Rate: {analysis['bounce_rate']:.2f}%")
                print(f"  📭 Unsubscribe Rate: {analysis['unsubscribe_rate']:.2f}%")
        
        self.results = results
        return results
    
    def determine_winner(self, metric: str = 'open_rate') -> Tuple[str, Dict[str, Any]]:
        """Determine the winning variant based on a specific metric."""
        
        if not self.results:
            print("❌ No results available. Run analyze_all_variants first.")
            return None, None
        
        print(f"\n🏆 Determining winner based on: {metric}")
        print("=" * 40)
        
        # Find the best performing variant
        best_variant = None
        best_value = -1
        
        for variant_name, data in self.results.items():
            value = data.get(metric, 0)
            print(f"  {variant_name}: {value:.2f}")
            
            if value > best_value:
                best_value = value
                best_variant = variant_name
        
        if best_variant:
            print(f"\n🎉 Winner: {best_variant} with {metric}: {best_value:.2f}")
            return best_variant, self.results[best_variant]
        
        return None, None
    
    def generate_report(self) -> str:
        """Generate a comprehensive A/B test report."""
        
        if not self.results:
            return "No results available for report generation."
        
        report = f"""
📋 A/B TEST REPORT
{'='*60}
Test Name: {self.test_name}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*60}

VARIANT COMPARISON:
"""
        
        # Create comparison table
        metrics = ['open_rate', 'click_rate', 'bounce_rate', 'unsubscribe_rate']
        metric_names = ['Open Rate', 'Click Rate', 'Bounce Rate', 'Unsubscribe Rate']
        
        for i, metric in enumerate(metrics):
            report += f"\n{metric_names[i]}:\n"
            for variant_name, data in self.results.items():
                value = data.get(metric, 0)
                report += f"  {variant_name}: {value:.2f}%\n"
        
        # Determine winners for each metric
        report += "\nWINNERS BY METRIC:\n"
        for i, metric in enumerate(metrics):
            winner, _ = self.determine_winner(metric)
            if winner:
                report += f"  {metric_names[i]}: {winner}\n"
        
        # Overall winner
        overall_winner, _ = self.determine_winner('open_rate')
        if overall_winner:
            report += f"\n🏆 OVERALL WINNER: {overall_winner}\n"
        
        return report

def create_subject_line_test(client: AcumbamailClient, list_id: int):
    """Create an A/B test for subject lines."""
    
    print("🧪 SUBJECT LINE A/B TEST")
    print("=" * 60)
    
    # Create A/B test
    ab_test = ABTest(client, "Subject Line Test", list_id)
    
    # Add variants
    ab_test.add_variant(
        name="Control",
        subject="New features just released!",
        content="""
        <h1>New Features Released</h1>
        <p>We've just released some exciting new features that we think you'll love!</p>
        <h2>What's New:</h2>
        <ul>
            <li>Enhanced dashboard</li>
            <li>Improved analytics</li>
            <li>Better mobile experience</li>
        </ul>
        <p>Try them out and let us know what you think!</p>
        """,
        pre_header="Check out our latest features"
    )
    
    ab_test.add_variant(
        name="Question",
        subject="Want to see what's new?",
        content="""
        <h1>New Features Released</h1>
        <p>We've just released some exciting new features that we think you'll love!</p>
        <h2>What's New:</h2>
        <ul>
            <li>Enhanced dashboard</li>
            <li>Improved analytics</li>
            <li>Better mobile experience</li>
        </ul>
        <p>Try them out and let us know what you think!</p>
        """,
        pre_header="Check out our latest features"
    )
    
    ab_test.add_variant(
        name="Urgency",
        subject="Limited time: New features available now!",
        content="""
        <h1>New Features Released</h1>
        <p>We've just released some exciting new features that we think you'll love!</p>
        <h2>What's New:</h2>
        <ul>
            <li>Enhanced dashboard</li>
            <li>Improved analytics</li>
            <li>Better mobile experience</li>
        </ul>
        <p>Try them out and let us know what you think!</p>
        """,
        pre_header="Check out our latest features"
    )
    
    return ab_test

def create_content_test(client: AcumbamailClient, list_id: int):
    """Create an A/B test for email content."""
    
    print("🧪 CONTENT A/B TEST")
    print("=" * 60)
    
    # Create A/B test
    ab_test = ABTest(client, "Content Test", list_id)
    
    # Add variants
    ab_test.add_variant(
        name="Short",
        subject="Quick update for you",
        content="""
        <h1>Quick Update</h1>
        <p>We've released new features!</p>
        <p><a href="https://example.com/features">Learn More</a></p>
        """,
        pre_header="Quick update about new features"
    )
    
    ab_test.add_variant(
        name="Detailed",
        subject="Quick update for you",
        content="""
        <h1>New Features Released</h1>
        <p>We're excited to announce the release of several new features that will enhance your experience:</p>
        
        <h2>Enhanced Dashboard</h2>
        <p>Our new dashboard provides better insights and easier navigation. You can now customize your view and get real-time updates.</p>
        
        <h2>Improved Analytics</h2>
        <p>Get deeper insights into your data with our enhanced analytics. Track performance, identify trends, and make data-driven decisions.</p>
        
        <h2>Better Mobile Experience</h2>
        <p>Enjoy a seamless experience on all devices with our improved mobile interface.</p>
        
        <p><a href="https://example.com/features">Learn More About These Features</a></p>
        
        <p>We'd love to hear your feedback!</p>
        """,
        pre_header="Detailed overview of our latest features"
    )
    
    return ab_test

def create_send_time_test(client: AcumbamailClient, list_id: int):
    """Create an A/B test for send times."""
    
    print("🧪 SEND TIME A/B TEST")
    print("=" * 60)
    
    # Create A/B test
    ab_test = ABTest(client, "Send Time Test", list_id)
    
    # Calculate different send times
    now = datetime.now()
    morning_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
    afternoon_time = now.replace(hour=14, minute=0, second=0, microsecond=0)
    evening_time = now.replace(hour=18, minute=0, second=0, microsecond=0)
    
    # Add variants with different send times
    ab_test.add_variant(
        name="Morning (9 AM)",
        subject="Start your day with our latest updates",
        content="""
        <h1>Good Morning!</h1>
        <p>Start your day with our latest updates and insights.</p>
        <p>We've got some exciting news to share with you!</p>
        """,
        pre_header="Morning updates and insights"
    )
    
    ab_test.add_variant(
        name="Afternoon (2 PM)",
        subject="Afternoon update: What's new",
        content="""
        <h1>Afternoon Update</h1>
        <p>Here's what's new and happening in our world.</p>
        <p>Take a break and catch up on the latest!</p>
        """,
        pre_header="Afternoon updates and insights"
    )
    
    ab_test.add_variant(
        name="Evening (6 PM)",
        subject="Evening wrap-up: Today's highlights",
        content="""
        <h1>Evening Wrap-up</h1>
        <p>Here's a summary of today's highlights and updates.</p>
        <p>Perfect reading for your evening routine!</p>
        """,
        pre_header="Evening summary and highlights"
    )
    
    return ab_test

def main():
    """Main function to demonstrate A/B testing."""
    
    # Initialize client
    client = AcumbamailClient(
        auth_token=os.getenv("ACUMBAMAIL_AUTH_TOKEN"),
        default_sender_name="A/B Testing Example",
        default_sender_email="abtest@example.com"
    )
    
    try:
        print("🧪 A/B Testing Example")
        print("=" * 60)
        
        # Get or create a test list
        print("📋 Setting up test list...")
        lists = client.get_lists()
        
        if not lists:
            print("Creating a new test list...")
            test_list = client.create_list(
                name="A/B Testing List",
                description="List for A/B testing experiments"
            )
        else:
            test_list = lists[0]
            print(f"Using existing list: {test_list.name}")
        
        print(f"✅ Using list: {test_list.name} (ID: {test_list.id})")
        
        # Example 1: Subject Line Test
        print(f"\n{'='*60}")
        print("EXAMPLE 1: SUBJECT LINE A/B TEST")
        print("=" * 60)
        
        subject_test = create_subject_line_test(client, test_list.id)
        campaigns = subject_test.create_test_campaigns()
        
        if campaigns:
            # Wait for results (simulated)
            subject_test.wait_for_results(wait_hours=1)
            
            # Analyze results
            subject_test.analyze_all_variants(campaigns)
            
            # Determine winner
            winner, winner_data = subject_test.determine_winner('open_rate')
            
            # Generate report
            print(subject_test.generate_report())
        
        # Example 2: Content Test
        print(f"\n{'='*60}")
        print("EXAMPLE 2: CONTENT A/B TEST")
        print("=" * 60)
        
        content_test = create_content_test(client, test_list.id)
        campaigns = content_test.create_test_campaigns()
        
        if campaigns:
            # Wait for results (simulated)
            content_test.wait_for_results(wait_hours=1)
            
            # Analyze results
            content_test.analyze_all_variants(campaigns)
            
            # Determine winner
            winner, winner_data = content_test.determine_winner('click_rate')
            
            # Generate report
            print(content_test.generate_report())
        
        print(f"\n{'='*60}")
        print("✅ A/B Testing Examples Completed")
        print("=" * 60)
        print("Note: In a real scenario, you would wait for actual time to pass")
        print("and collect real campaign data before analyzing results.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 