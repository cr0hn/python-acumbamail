#!/usr/bin/env python3
"""
Automated Workflows Example

This example demonstrates how to implement automated email workflows
including welcome series, drip campaigns, and triggered emails.
"""

import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from acumbamail import AcumbamailClient

class EmailWorkflow:
    """Base class for email workflows."""
    
    def __init__(self, client: AcumbamailClient, name: str, list_id: int):
        self.client = client
        self.name = name
        self.list_id = list_id
        self.campaigns = []
    
    def add_campaign(self, name: str, subject: str, content: str, delay_days: int = 0, pre_header: str = None):
        """Add a campaign to the workflow."""
        self.campaigns.append({
            'name': name,
            'subject': subject,
            'content': content,
            'delay_days': delay_days,
            'pre_header': pre_header
        })
    
    def create_workflow_campaigns(self) -> List[Dict[str, Any]]:
        """Create all campaigns in the workflow."""
        
        print(f"📧 Creating workflow campaigns for: {self.name}")
        print("=" * 60)
        
        created_campaigns = []
        
        for i, campaign_data in enumerate(self.campaigns, 1):
            try:
                # Calculate scheduled time
                scheduled_time = None
                if campaign_data['delay_days'] > 0:
                    scheduled_time = datetime.now() + timedelta(days=campaign_data['delay_days'])
                
                campaign = self.client.create_campaign(
                    name=f"{self.name} - {campaign_data['name']}",
                    subject=campaign_data['subject'],
                    content=campaign_data['content'],
                    list_ids=[self.list_id],
                    pre_header=campaign_data.get('pre_header'),
                    scheduled_at=scheduled_time
                )
                
                print(f"✅ Campaign {i}: {campaign_data['name']}")
                if scheduled_time:
                    print(f"   📅 Scheduled for: {scheduled_time.strftime('%Y-%m-%d %H:%M')}")
                else:
                    print(f"   📅 Sending immediately")
                
                created_campaigns.append({
                    'workflow_name': self.name,
                    'campaign_name': campaign_data['name'],
                    'campaign_id': campaign.id,
                    'scheduled_time': scheduled_time,
                    'campaign': campaign
                })
                
            except Exception as e:
                print(f"❌ Failed to create campaign {i}: {campaign_data['name']} - {str(e)}")
        
        return created_campaigns

class WelcomeSeries(EmailWorkflow):
    """Welcome series workflow for new subscribers."""
    
    def __init__(self, client: AcumbamailClient, list_id: int):
        super().__init__(client, "Welcome Series", list_id)
        self._setup_welcome_series()
    
    def _setup_welcome_series(self):
        """Setup the welcome series campaigns."""
        
        # Day 0: Welcome email (immediate)
        self.add_campaign(
            name="Welcome Email",
            subject="Welcome to our community! 🎉",
            content="""
            <h1>Welcome to Our Community!</h1>
            <p>Hi there!</p>
            <p>We're thrilled to have you join our community. You're now part of something special!</p>
            
            <h2>What to expect:</h2>
            <ul>
                <li>📧 Regular updates and insights</li>
                <li>🎯 Exclusive content and tips</li>
                <li>💡 Industry best practices</li>
                <li>🚀 Early access to new features</li>
            </ul>
            
            <p>In the next few days, we'll send you some helpful resources to get started.</p>
            
            <p>Thanks for joining us!</p>
            <p>Best regards,<br>The Team</p>
            """,
            delay_days=0,
            pre_header="Welcome to our community! We're excited to have you on board."
        )
        
        # Day 1: Getting started guide
        self.add_campaign(
            name="Getting Started Guide",
            subject="Getting started: Your quick start guide",
            content="""
            <h1>Getting Started Guide</h1>
            <p>Now that you're part of our community, let's get you started!</p>
            
            <h2>Quick Start Checklist:</h2>
            <ol>
                <li><strong>Explore our platform</strong> - Take a tour of our features</li>
                <li><strong>Complete your profile</strong> - Add your preferences</li>
                <li><strong>Join our community</strong> - Connect with other members</li>
                <li><strong>Set up notifications</strong> - Stay updated on what matters</li>
            </ol>
            
            <h2>Need Help?</h2>
            <p>Our support team is here to help you get the most out of our platform.</p>
            <p><a href="https://example.com/support">Get Support</a></p>
            
            <p>Happy exploring!</p>
            """,
            delay_days=1,
            pre_header="Your quick start guide to getting the most out of our platform"
        )
        
        # Day 3: First value email
        self.add_campaign(
            name="First Value Email",
            subject="Here's something valuable for you",
            content="""
            <h1>Exclusive Content Just for You</h1>
            <p>As a member of our community, you get access to exclusive content and insights.</p>
            
            <h2>This Week's Highlights:</h2>
            <ul>
                <li><strong>Industry Report:</strong> Latest trends and insights</li>
                <li><strong>Expert Tips:</strong> Best practices from industry leaders</li>
                <li><strong>Case Study:</strong> How others are succeeding</li>
            </ul>
            
            <p><a href="https://example.com/exclusive-content">Read the Full Report</a></p>
            
            <p>We'll continue to share valuable content like this regularly.</p>
            """,
            delay_days=3,
            pre_header="Exclusive content and insights just for our community members"
        )
        
        # Day 7: Feedback request
        self.add_campaign(
            name="Feedback Request",
            subject="How are we doing? We'd love your feedback",
            content="""
            <h1>How Are We Doing?</h1>
            <p>You've been with us for a week now, and we'd love to hear your thoughts!</p>
            
            <p>Your feedback helps us improve and provide better value to our community.</p>
            
            <h2>Quick Questions:</h2>
            <ul>
                <li>How are you finding our content?</li>
                <li>What topics would you like to see more of?</li>
                <li>How can we better serve your needs?</li>
            </ul>
            
            <p><a href="https://example.com/feedback">Share Your Feedback</a></p>
            
            <p>Thank you for being part of our community!</p>
            """,
            delay_days=7,
            pre_header="We'd love to hear your feedback to improve our service"
        )

class DripCampaign(EmailWorkflow):
    """Drip campaign for lead nurturing."""
    
    def __init__(self, client: AcumbamailClient, list_id: int, product_name: str = "Our Product"):
        super().__init__(client, f"Drip Campaign - {product_name}", list_id)
        self.product_name = product_name
        self._setup_drip_campaign()
    
    def _setup_drip_campaign(self):
        """Setup the drip campaign sequence."""
        
        # Day 0: Introduction
        self.add_campaign(
            name="Introduction",
            subject=f"Discover {self.product_name}",
            content=f"""
            <h1>Discover {self.product_name}</h1>
            <p>Hi there!</p>
            <p>We noticed you're interested in {self.product_name}. We'd love to show you how it can help you achieve your goals.</p>
            
            <h2>What is {self.product_name}?</h2>
            <p>{self.product_name} is designed to solve your biggest challenges and help you succeed.</p>
            
            <p><a href="https://example.com/product">Learn More</a></p>
            
            <p>In the coming days, we'll share more insights about how {self.product_name} can benefit you.</p>
            """,
            delay_days=0,
            pre_header=f"Discover how {self.product_name} can help you succeed"
        )
        
        # Day 2: Problem awareness
        self.add_campaign(
            name="Problem Awareness",
            subject="Are you facing these challenges?",
            content=f"""
            <h1>Common Challenges We Solve</h1>
            <p>Many of our customers face similar challenges before discovering {self.product_name}.</p>
            
            <h2>Do any of these sound familiar?</h2>
            <ul>
                <li>Struggling with inefficient processes</li>
                <li>Looking for better ways to manage your workflow</li>
                <li>Wanting to improve productivity and results</li>
                <li>Needing more reliable solutions</li>
            </ul>
            
            <p>If you're facing any of these challenges, {self.product_name} might be the solution you've been looking for.</p>
            
            <p><a href="https://example.com/challenges">See How We Solve These</a></p>
            """,
            delay_days=2,
            pre_header="Discover how we solve common challenges in your industry"
        )
        
        # Day 5: Solution presentation
        self.add_campaign(
            name="Solution Presentation",
            subject=f"How {self.product_name} solves your problems",
            content=f"""
            <h1>How {self.product_name} Solves Your Problems</h1>
            <p>Now that we've identified the challenges, let's see how {self.product_name} provides solutions.</p>
            
            <h2>Key Benefits:</h2>
            <ul>
                <li><strong>Increased Efficiency:</strong> Streamline your workflow</li>
                <li><strong>Better Results:</strong> Achieve your goals faster</li>
                <li><strong>Cost Savings:</strong> Reduce time and resource waste</li>
                <li><strong>Reliability:</strong> Dependable performance every time</li>
            </ul>
            
            <p><a href="https://example.com/benefits">Explore the Benefits</a></p>
            
            <p>Ready to see {self.product_name} in action?</p>
            """,
            delay_days=5,
            pre_header=f"See how {self.product_name} provides real solutions to your challenges"
        )
        
        # Day 8: Social proof
        self.add_campaign(
            name="Social Proof",
            subject="See what others are saying about us",
            content=f"""
            <h1>What Our Customers Say</h1>
            <p>Don't just take our word for it. Here's what our customers are saying about {self.product_name}.</p>
            
            <blockquote>
                "This has completely transformed how we work. Highly recommended!"
                <br>- Sarah Johnson, Marketing Director
            </blockquote>
            
            <blockquote>
                "The best solution we've found for our needs. Excellent support too!"
                <br>- Mike Chen, Operations Manager
            </blockquote>
            
            <blockquote>
                "Wish we had found this sooner. It's made a huge difference."
                <br>- Lisa Rodriguez, CEO
            </blockquote>
            
            <p><a href="https://example.com/testimonials">Read More Reviews</a></p>
            
            <p>Join thousands of satisfied customers who have transformed their workflow with {self.product_name}.</p>
            """,
            delay_days=8,
            pre_header="See what our customers are saying about their experience"
        )
        
        # Day 12: Call to action
        self.add_campaign(
            name="Call to Action",
            subject="Ready to get started? Here's your next step",
            content=f"""
            <h1>Ready to Get Started?</h1>
            <p>You've learned about the challenges, seen the solutions, and heard from our customers.</p>
            
            <p>Now it's time to take action and see how {self.product_name} can help you.</p>
            
            <h2>Your Next Steps:</h2>
            <ol>
                <li><strong>Schedule a Demo:</strong> See {self.product_name} in action</li>
                <li><strong>Start Free Trial:</strong> Try it risk-free for 14 days</li>
                <li><strong>Talk to Sales:</strong> Get personalized recommendations</li>
            </ol>
            
            <p><a href="https://example.com/get-started">Get Started Today</a></p>
            
            <p>Don't wait to start seeing results. Join thousands of satisfied customers today!</p>
            """,
            delay_days=12,
            pre_header="Take the next step and start seeing results with our solution"
        )

class TriggeredEmails:
    """Triggered email system for specific events."""
    
    def __init__(self, client: AcumbamailClient):
        self.client = client
        self.templates = {}
        self._setup_templates()
    
    def _setup_templates(self):
        """Setup email templates for different triggers."""
        
        # Order confirmation template
        self.templates['order_confirmation'] = {
            'subject': 'Order Confirmation - Order #{order_number}',
            'content': """
            <h1>Order Confirmation</h1>
            <p>Thank you for your order!</p>
            <p><strong>Order Number:</strong> #{order_number}</p>
            <p><strong>Order Date:</strong> {order_date}</p>
            <p><strong>Total Amount:</strong> ${total_amount}</p>
            
            <h2>Order Details:</h2>
            {order_items}
            
            <p>We'll send you a tracking number once your order ships.</p>
            <p>If you have any questions, please contact our support team.</p>
            """,
            'pre_header': 'Your order has been confirmed and is being processed'
        }
        
        # Password reset template
        self.templates['password_reset'] = {
            'subject': 'Password Reset Request',
            'content': """
            <h1>Password Reset Request</h1>
            <p>We received a request to reset your password.</p>
            <p>Click the link below to create a new password:</p>
            <p><a href="{reset_link}">Reset Password</a></p>
            <p>This link will expire in 24 hours.</p>
            <p>If you didn't request this, you can safely ignore this email.</p>
            """,
            'pre_header': 'Reset your password securely'
        }
        
        # Welcome back template
        self.templates['welcome_back'] = {
            'subject': 'Welcome back! We missed you',
            'content': """
            <h1>Welcome Back!</h1>
            <p>We noticed you haven't been around lately, and we wanted to check in.</p>
            <p>Here's what you've been missing:</p>
            <ul>
                <li>New features and updates</li>
                <li>Exclusive content and insights</li>
                <li>Community events and discussions</li>
            </ul>
            <p><a href="{login_link}">Log In Now</a></p>
            <p>We'd love to have you back!</p>
            """,
            'pre_header': 'We missed you! Come back and see what\'s new'
        }
    
    def send_triggered_email(self, trigger_type: str, to_email: str, **kwargs):
        """Send a triggered email based on the event type."""
        
        if trigger_type not in self.templates:
            raise ValueError(f"Unknown trigger type: {trigger_type}")
        
        template = self.templates[trigger_type]
        
        # Format the content with provided variables
        content = template['content'].format(**kwargs)
        subject = template['subject'].format(**kwargs)
        pre_header = template.get('pre_header', '').format(**kwargs)
        
        try:
            email_id = self.client.send_single_email(
                to_email=to_email,
                subject=subject,
                content=content,
                category=trigger_type
            )
            
            print(f"✅ Triggered email sent: {trigger_type} to {to_email} (ID: {email_id})")
            return email_id
            
        except Exception as e:
            print(f"❌ Failed to send triggered email: {trigger_type} to {to_email} - {str(e)}")
            return None

def main():
    """Main function to demonstrate automated workflows."""
    
    # Initialize client
    client = AcumbamailClient(
        auth_token=os.getenv("ACUMBAMAIL_AUTH_TOKEN"),
        default_sender_name="Automated Workflows Example",
        default_sender_email="workflows@example.com"
    )
    
    try:
        print("🤖 Automated Workflows Example")
        print("=" * 60)
        
        # Get or create test lists
        print("📋 Setting up test lists...")
        lists = client.get_lists()
        
        if not lists:
            print("Creating test lists...")
            welcome_list = client.create_list(
                name="Welcome Series List",
                description="List for welcome series testing"
            )
            drip_list = client.create_list(
                name="Drip Campaign List",
                description="List for drip campaign testing"
            )
        else:
            welcome_list = lists[0]
            drip_list = lists[1] if len(lists) > 1 else lists[0]
            print(f"Using existing lists: {welcome_list.name}, {drip_list.name}")
        
        # Example 1: Welcome Series
        print(f"\n{'='*60}")
        print("EXAMPLE 1: WELCOME SERIES")
        print("=" * 60)
        
        welcome_series = WelcomeSeries(client, welcome_list.id)
        welcome_campaigns = welcome_series.create_workflow_campaigns()
        
        print(f"\n✅ Created {len(welcome_campaigns)} welcome series campaigns")
        
        # Example 2: Drip Campaign
        print(f"\n{'='*60}")
        print("EXAMPLE 2: DRIP CAMPAIGN")
        print("=" * 60)
        
        drip_campaign = DripCampaign(client, drip_list.id, "SuperTool Pro")
        drip_campaigns = drip_campaign.create_workflow_campaigns()
        
        print(f"\n✅ Created {len(drip_campaigns)} drip campaign emails")
        
        # Example 3: Triggered Emails
        print(f"\n{'='*60}")
        print("EXAMPLE 3: TRIGGERED EMAILS")
        print("=" * 60)
        
        triggered_emails = TriggeredEmails(client)
        
        # Send different types of triggered emails
        print("Sending triggered emails...")
        
        # Order confirmation
        triggered_emails.send_triggered_email(
            'order_confirmation',
            'customer@example.com',
            order_number='12345',
            order_date='2024-03-20',
            total_amount='99.99',
            order_items='<li>Product A - $49.99</li><li>Product B - $50.00</li>'
        )
        
        # Password reset
        triggered_emails.send_triggered_email(
            'password_reset',
            'user@example.com',
            reset_link='https://example.com/reset?token=abc123'
        )
        
        # Welcome back
        triggered_emails.send_triggered_email(
            'welcome_back',
            'returning@example.com',
            login_link='https://example.com/login'
        )
        
        print(f"\n{'='*60}")
        print("✅ Automated Workflows Examples Completed")
        print("=" * 60)
        print("Note: In a real scenario, these workflows would be triggered")
        print("by actual user actions and events in your application.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 