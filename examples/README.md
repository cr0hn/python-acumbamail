# Acumbamail SDK — Examples

Ready-to-run examples demonstrating the main features of the SDK.

## Requirements

```bash
pip install acumbamail
export ACUMBAMAIL_TOKEN="tu_token_aqui"
```

> The token can be obtained from your Acumbamail account → Settings → API.

## Available examples

### `example-001.py` — Hello World

The simplest possible example: list your mailing lists and add a subscriber.
Recommended starting point for getting familiar with the SDK.

```bash
python examples/example-001.py
```

---

### `sync_example.py` — Basic synchronous client

Shows the most common operations with `AcumbamailClient`:

- List mailing lists (`get_lists`)
- Add a subscriber (`add_subscriber`)
- Get subscribers (`get_subscribers`)
- Create a campaign with `*|UNSUBSCRIBE_URL|*` (`create_campaign`)
- View campaign statistics (`get_campaign_total_information`)

```bash
python examples/sync_example.py
```

---

### `async_example.py` — Asynchronous client

Equivalent to `sync_example.py` using `AsyncAcumbamailClient` with `async/await`.
Includes an example with a context manager (recommended) and without one.

```bash
python examples/async_example.py
```

---

### `campaign_analytics.py` — Campaign analytics

Campaign performance analysis:

- List campaigns (`get_campaigns`)
- Aggregate metrics: open rate, click rate, bounces (`get_campaign_total_information`)
- Most clicked URLs (`get_campaign_clicks`)
- Opens by browser (`get_campaign_openers_by_browser`)
- Opens by operating system (`get_campaign_openers_by_os`)

```bash
python examples/campaign_analytics.py
```

---

### `bulk_operations.py` — Bulk operations

Efficient management of large data volumes:

- Batch subscriber sign-up (`batch_add_subscribers`)
- Search for subscribers (`search_subscriber`)
- Inactive subscribers with details (`get_inactive_subscribers` with `full_info=True`)

```bash
python examples/bulk_operations.py
```

---

### `ab_testing.py` — A/B Testing

Creates two campaigns with different subjects for the same list and compares their statistics
(`get_campaign_total_information`) to determine which variant performs better.

**WARNING:** creates real campaigns in your account.

```bash
python examples/ab_testing.py
```

---

### `automated_workflows.py` — Automated workflows

Complete automation flow:

1. Create a list (`create_list`)
2. Bulk subscriber sign-up (`batch_add_subscribers`)
3. Create a welcome campaign (`create_campaign`)
4. Query statistics (`get_campaign_total_information`)
5. Configure a list webhook (`config_list_webhook` — commented out by default)

**WARNING:** creates real lists, subscribers, and campaigns in your account.

```bash
python examples/automated_workflows.py
```

---

### `error_handling.py` — Error handling

SDK error handling patterns:

- `AcumbamailValidationError` — invalid email, campaign missing `*|UNSUBSCRIBE_URL|*`
- `AcumbamailAPIError` — errors returned by the API
- `AcumbamailRateLimitError` — request limit exceeded (the SDK retries automatically)
- Graceful degradation with a fallback strategy
- Batch operations with partial errors

```bash
python examples/error_handling.py
```

---

## Important notes

- **Token:** always use `ACUMBAMAIL_TOKEN` (not `ACUMBAMAIL_AUTH_TOKEN`).
- **UNSUBSCRIBE_URL:** all campaign content must include `*|UNSUBSCRIBE_URL|*` or the API will reject it.
- **Test list ID:** examples use `1138335` by default; replace it with the ID of a real list from your account.
- **Destructive operations:** examples that create or delete data are marked with the **WARNING** notice.
- **Rate limiting:** the SDK automatically retries requests that receive HTTP 429 (3 attempts with 10s backoff).
