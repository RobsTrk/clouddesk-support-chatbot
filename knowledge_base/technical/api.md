# CloudDesk API authentication and webhook errors
Category: technical
Intent: api

## API authentication
Use a current API key from the workspace's API settings and send it in the documented authentication header. Never paste API keys into a chat or ticket.

## Webhook 403 responses
A 403 means the receiving endpoint rejected the webhook request. Verify that the endpoint accepts CloudDesk requests, that any allowlist or authentication requirement is configured, and that the endpoint URL is correct.

## Escalation conditions
If those checks do not resolve the 403, collect the webhook event type, approximate timestamp, endpoint host (not secrets), and response identifier, then escalate. Nova must not invent endpoint-specific settings.
