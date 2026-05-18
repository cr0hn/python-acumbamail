---
name: acumbamail-cli
description: Use when working with the Acumbamail CLI (`acumbamail` command) to manage email marketing lists, subscribers, campaigns, and webhooks from the terminal or in scripts. Covers all subcommands, authentication, JSON output, and common automation workflows.
---

# Acumbamail CLI

The `acumbamail` CLI manages [Acumbamail](https://acumbamail.com) email marketing from the terminal. All output is JSON on stdout; errors go to stderr with exit code 1.

## Authentication

Two methods, resolved in this order:

1. **`--token` flag** — takes precedence
2. **`ACUMBAMAIL_TOKEN` env var** — used when flag is absent

```bash
export ACUMBAMAIL_TOKEN=YOUR_TOKEN_HERE

# or per-command:
acumbamail --token YOUR_TOKEN_HERE lists list
```

## Command Groups

### `lists` — Mailing list management

```bash
# List all available lists
acumbamail lists list
# → [{"id": 123, "name": "Newsletter", "subscribers_count": 500, ...}]

# Create a new list
acumbamail lists create --name "My List" --sender-email sender@example.com
acumbamail lists create --name "My List" --sender-email sender@example.com --description "Weekly digest"
# → {"id": 456, "name": "My List", "description": ""}

# Delete a list
acumbamail lists delete --list-id 456
# → {"deleted": true, "list_id": 456}

# Get stats for a list
acumbamail lists stats --list-id 123
# → {"total_subscribers": 500, "unsubscribed_subscribers": 12, "hard_bounced_subscribers": 3, ...}
```

### `subscribers` — Subscriber management

```bash
# List subscribers in a list
acumbamail subscribers list --list-id 123
# → [{"email": "user@x.com", "list_id": 123, "is_active": true, "fields": {...}}, ...]

# Add a single subscriber
acumbamail subscribers add --list-id 123 --email user@example.com
acumbamail subscribers add --list-id 123 --email user@example.com --fields '{"name": "John", "company": "Acme"}'
# → {"email": "user@example.com", "list_id": 123}

# Delete a subscriber
acumbamail subscribers delete --list-id 123 --email user@example.com
# → {"deleted": true, "email": "user@example.com", "list_id": 123}

# Search across all lists
acumbamail subscribers search --query user@example.com
# → [{"email": "user@example.com", "status": "active", "list_id": 123, "id": 456}, ...]

# Unsubscribe (marks inactive, does not delete)
acumbamail subscribers unsubscribe --list-id 123 --email user@example.com
# → {"unsubscribed": true, "email": "user@example.com", "list_id": 123}

# Bulk import from JSON file
# File format: [{"email": "a@x.com"}, {"email": "b@x.com", "name": "Bob"}]
acumbamail subscribers batch-add --list-id 123 --file subscribers.json
acumbamail subscribers batch-add --list-id 123 --file subscribers.json --update  # update existing
# → [{"email": "a@x.com", "subscriber_id": 111}, {"email": "b@x.com", "subscriber_id": 222}]
```

### `campaigns` — Campaign analytics

```bash
# List all campaigns
acumbamail campaigns list
# → [{"id": 1, "name": "Newsletter #1", "subject": "...", "from_email": "...", "list_ids": [123]}, ...]

# Get basic campaign info
acumbamail campaigns info --campaign-id 999
# → {"id": 999, "name": "...", "subject": "...", ...}

# Get full campaign stats
acumbamail campaigns stats --campaign-id 999
# → {
#     "total_delivered": 490, "emails_to_send": 500,
#     "opened": 120, "unique_clicks": 45, "total_clicks": 62,
#     "hard_bounces": 8, "soft_bounces": 2,
#     "unsubscribes": 3, "complaints": 0,
#     "unopened": 370, "campaign_url": "https://..."
#   }
```

### `webhooks` — Webhook configuration

```bash
# Get current SMTP webhook config
acumbamail webhooks smtp-get
# → {"id": 87492, "url": "https://...", "active": true, "delivered": true, "hard_bounces": false, ...}

# Configure SMTP webhook
acumbamail webhooks smtp-config --url https://myapp.com/webhooks/smtp \
  --delivered --hard-bounce --active
acumbamail webhooks smtp-config --url https://myapp.com/webhooks/smtp --no-active  # disable

# Get current list webhook config
acumbamail webhooks list-get --list-id 123
# → {"id": 102650, "url": "https://...", "active": false, "subscribes": true, "unsubscribes": true, ...}

# Configure list webhook
acumbamail webhooks list-config --list-id 123 \
  --url https://myapp.com/webhooks/list \
  --subscribes --unsubscribes --active
```

## Output Format

All commands output **JSON on stdout**. Use `jq` for filtering:

```bash
# Get list of list IDs
acumbamail lists list | jq '[.[].id]'

# Get total subscribers across all lists
acumbamail lists list | jq '[.[].subscribers_count] | add'

# Check if a subscriber exists
acumbamail subscribers search --query user@example.com | jq 'length > 0'

# Get open rate for a campaign
acumbamail campaigns stats --campaign-id 999 | \
  jq '.opened / .total_delivered * 100 | round | tostring + "%"'
```

## Error Handling

```bash
# Errors go to stderr, exit code 1
acumbamail lists list 2>errors.log
if [ $? -ne 0 ]; then echo "API call failed"; fi

# Capture both
output=$(acumbamail campaigns stats --campaign-id 999 2>&1)
```

## Common Workflows

### Add subscribers from CSV

```bash
# Convert CSV to JSON first, then import
python3 -c "
import csv, json, sys
rows = list(csv.DictReader(sys.stdin))
print(json.dumps(rows))
" < subscribers.csv > subscribers.json

acumbamail subscribers batch-add --list-id 123 --file subscribers.json --update
```

### Monitor campaign performance

```bash
CAMPAIGN_ID=999
stats=$(acumbamail campaigns stats --campaign-id $CAMPAIGN_ID)
echo "Open rate: $(echo $stats | jq '.opened / .total_delivered * 100 | round')%"
echo "Click rate: $(echo $stats | jq '.unique_clicks / .total_delivered * 100 | round')%"
```

### Set up webhook for new subscribers

```bash
acumbamail webhooks list-config \
  --list-id 123 \
  --url https://myapp.com/api/webhooks/acumbamail \
  --subscribes --unsubscribes \
  --active
```

## Install / Update Skills

```bash
# Install skills locally (current project)
acumbamail install-skills

# Install skills globally
acumbamail install-skills -g
```
