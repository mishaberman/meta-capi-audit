# Meta Conversions API (CAPI) Best Practices Reference

This document contains the condensed knowledge base for evaluating and improving Meta Conversions API implementations. Use it when writing the business impact and developer action plan sections of the audit report.

## Setup Architecture

The **Redundant Setup** (Pixel + CAPI together) is Meta's recommended architecture. It provides maximum event coverage and reliability because browser-side tracking captures real-time user interactions while server-side tracking bypasses ad blockers and browser privacy restrictions. When using a redundant setup, **deduplication is mandatory** to prevent double-counting events.

A **CAPI-only setup** is acceptable but less preferred. It misses real-time browser interactions and requires the server to capture all user data. A **Pixel-only setup** is the weakest because it is vulnerable to ad blockers, iOS privacy changes, and cookie restrictions that can cause 20–40% data loss.

## Implementation Methods

There are two primary methods for making CAPI calls directly from your own server code:

1. **Direct HTTP API:** Pure HTTP requests (`fetch`, `axios`, `requests`, `curl`) to `graph.facebook.com/v{version}/{pixel_id}/events`. This is the most flexible approach but requires manual hashing, cookie extraction, and payload construction.
2. **Meta Business SDK:** The official SDKs (Node.js, Python, PHP, Ruby, Java) that provide strongly typed classes (`EventRequest`, `ServerEvent`, `UserData`) and handle some of the payload construction for you.

In addition, the **Parameter Builder Library** (`capi-param-builder`) is an assist library that can be used alongside either method above. It automatically handles cookie extraction, IP address formatting (IPv6 preferred), PII normalization and hashing, and uses a combined client-side and server-side workflow to maximize match keys. It is the recommended assist for new setups.

*Note: Partner integrations (Shopify, WooCommerce, GTM Server-Side, etc.) are out of scope for this skill. This skill audits direct integrations only.*

## Event Match Quality (EMQ)

EMQ measures how well Meta can match events to user profiles for ad optimization and attribution. The score ranges from 0 to 10.

| Score Range | Rating | Implication |
|-------------|--------|-------------|
| 8.0–10.0 | Great | Optimal ad delivery and attribution |
| 6.0–7.9 | Good | Acceptable, but improvement will reduce CPA |
| 4.0–5.9 | OK | Significant attribution gaps, higher CPA |
| 0.0–3.9 | Poor | Severely limited optimization capability |

### EMQ Parameter Categories

To reach the EMQ threshold, implement parameters in this priority order:

**Foundation (MUST — target 100% coverage):** These are non-PII parameters that should be sent with every event. Missing any of these undermines the entire matching pipeline.

| Parameter | CAPI Field | Hash? | Impact |
|-----------|-----------|-------|--------|
| IP Address | `client_ip_address` | No | Critical for Identity Prediction (~70% match rate) |
| User Agent | `client_user_agent` | No | Critical for Identity Prediction (~70% match rate) |
| Browser ID | `fbp` (from `_fbp` cookie) | No | +0.5–1 EMQ point |

**Click ID (target: match browser coverage):** The `fbc` parameter (from the `_fbc` cookie) provides a 100% match rate when present. It is a **HIGH priority** parameter, on par with email.

| Parameter | CAPI Field | Hash? | Impact |
|-----------|-----------|-------|--------|
| Click ID | `fbc` (from `_fbc` cookie) | No | HIGH priority, 100% match rate |

**High PII (send one close to 100%):** Email and phone are the highest-impact PII parameters. Sending just one of them close to 100% coverage can improve EMQ by 2–3 points.

| Parameter | CAPI Field | Hash? | Impact |
|-----------|-----------|-------|--------|
| Email | `em` | SHA-256 | +2–3 EMQ points |
| Phone | `ph` | SHA-256 | +2–3 EMQ points |

**Medium PII (send one close to 100%):** Sending just one medium PII parameter close to 100% adds approximately 0.5 EMQ points.

| Parameter | CAPI Field | Hash? | Impact |
|-----------|-----------|-------|--------|
| First Name | `fn` | SHA-256 | +0.5 EMQ point |
| Last Name | `ln` | SHA-256 | +0.5 EMQ point |
| Date of Birth | `db` | SHA-256 | +0.5 EMQ point |
| City | `ct` | SHA-256 | +0.25 EMQ point |
| Zip Code | `zp` | SHA-256 | +0.25 EMQ point |

## Hashing Requirements

All PII parameters must be normalized and hashed with SHA-256 before sending. The normalization steps are: convert to lowercase, trim leading/trailing whitespace, and encode as UTF-8. Never send empty or null values — omit the field entirely if the data is unavailable.

Parameters that must NOT be hashed: `client_ip_address`, `client_user_agent`, `fbc`, `fbp`, `external_id`.

## Deduplication

The recommended method is **Event ID + Event Name**. Both the browser pixel and the server CAPI must send the same unique identifier for each event instance:

- Browser: `fbq('track', 'Purchase', {value: 12, currency: 'USD'}, {eventID: 'unique-123'})`
- Server: `event_id: 'unique-123'` in the CAPI payload

The `event_name` must also match exactly (case-sensitive). Events are deduplicated within a 48-hour window.

For redundant setups, **Event Coverage** (server events / browser events) should be >= 90%, and **Deduplication Overlap** should be >= 50%.

## Testing & Validation Tools

1. **Test Events Tool:** Found in Events Manager. Generates a `test_event_code` to include in CAPI payloads. Validates `event_id`, customer info params, custom params, and dedup status. Events appear within 30 seconds.
2. **Payload Helper:** Validates CAPI payload structure before sending and generates code snippets.
3. **Network Console:** Verify `event_id` in network traffic to ensure browser and server IDs match exactly.

## Common Code Patterns by Framework

**Next.js / React:** CAPI calls are made from API routes (`pages/api/` or `app/api/`). The `_fbc` and `_fbp` cookies can be read server-side from the request headers.

**Django / Flask:** CAPI calls are made from view functions or middleware. `request.META['REMOTE_ADDR']` provides IP, `request.META['HTTP_USER_AGENT']` provides UA, and `request.COOKIES.get('_fbc')` provides the click ID.

**Express.js:** CAPI calls from route handlers. `req.ip` for IP, `req.headers['user-agent']` for UA, `req.cookies._fbc` for click ID (requires `cookie-parser` middleware).

**PHP / Laravel:** CAPI calls from controllers. `$_SERVER['REMOTE_ADDR']` for IP, `$_SERVER['HTTP_USER_AGENT']` for UA, `$_COOKIE['_fbc']` for click ID.
