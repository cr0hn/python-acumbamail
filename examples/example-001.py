from acumbamail import AcumbamailClient

# Initialize the client
client = AcumbamailClient(
    auth_token='41b0f45e437c4028ad9e33f1ce7c7313',
    default_sender_name='Dani',
    default_sender_email='cr0hn@cr0hn.com'
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