# Meta Pixel & CAPI Best Practices Reference

This document contains the condensed knowledge base for evaluating and improving Meta Pixel and Conversions API implementations. Use it when writing the business impact and developer action plan sections of the audit report.

## Setup Architecture

The **Redundant Setup** (Pixel + CAPI together) is Meta's recommended architecture. It provides maximum event coverage and reliability because browser-side tracking captures real-time user interactions while server-side tracking bypasses ad blockers and browser privacy restrictions. When using a redundant setup, **deduplication is mandatory** to prevent double-counting events.

A **CAPI-only setup** is acceptable but less preferred. It misses real-time browser interactions and requires the server to capture all user data. A **Pixel-only setup** is the weakest because it is vulnerable to ad blockers, iOS privacy changes, and cookie restrictions that can cause 20–40% data loss.

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
| IP Address | `client_ip_address` | No | Baseline matching |
| User Agent | `client_user_agent` | No | Baseline matching |
| Browser ID | `fbp` (from `_fbp` cookie) | No | +0.5–1 EMQ point |

Note: Either `fbp` (Browser ID) or `external_id` is sufficient. Sending both does not add additional EMQ benefit.

**Click ID (target: match browser coverage):** The `fbc` parameter (from the `_fbc` cookie) provides a 100% match rate when present. For redundant setups, server-side `fbc` coverage should match browser-side coverage. For CAPI-only setups, target 25% coverage.

| Parameter | CAPI Field | Hash? | Impact |
|-----------|-----------|-------|--------|
| Click ID | `fbc` (from `_fbc` cookie) | No | +0.5–1 EMQ point, 100% match rate |

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

The `event_name` must also match exactly (case-sensitive). Events are deduplicated within a 48-hour window. The alternative method (using `fbp`/`external_id`) is less reliable and only works when the browser event arrives before the server event.

For redundant setups, **Event Coverage** (server events / browser events) should be >= 100%, and **Deduplication Overlap** should be >= 75%.

## Standard Events by Business Type

| Business Type | Expected Events |
|---------------|----------------|
| E-commerce | PageView, ViewContent, AddToCart, InitiateCheckout, AddPaymentInfo, Purchase |
| Lead Generation | PageView, ViewContent, Lead, CompleteRegistration, Contact |
| SaaS / Subscription | PageView, ViewContent, Lead, StartTrial, Subscribe, Purchase |
| Content / Media | PageView, ViewContent, Search |

## Standard Events Parameter Reference

| Event | Required Params | Key Optional Params | Business Purpose |
|-------|----------------|--------------------|--------------------|
| PageView | — | — | Baseline tracking, audience building |
| ViewContent | — | `content_ids`, `value`, `currency` | Product interest, dynamic ads |
| AddToCart | — | `content_ids`, `value`, `currency` | Purchase intent, dynamic ads |
| InitiateCheckout | — | `value`, `currency`, `num_items` | Funnel optimization |
| AddPaymentInfo | — | `value`, `currency` | Funnel optimization |
| Purchase | `value`, `currency` | `content_ids`, `content_type` | ROAS optimization, dynamic ads |
| Lead | — | `value`, `currency` | Lead generation optimization |
| CompleteRegistration | — | `value`, `currency` | Sign-up tracking |
| Search | — | `search_string`, `content_ids` | Search behavior, dynamic ads |
| Subscribe | — | `value`, `currency`, `predicted_ltv` | Subscription optimization |
| StartTrial | — | `value`, `currency` | Trial-to-paid optimization |
| Contact | — | — | Lead generation |

## Great Setup Examples

**Redundant Setup (Gold Standard):**
- Event Coverage: 120%, Deduplication (event_id): 80% overlap
- Foundation: IP 100%, UA 100%, Browser ID 100%
- ClickID: Browser 10%, Server 10% (matched)
- High PII: Email 90%
- Medium PII: First Name 95%

**CAPI-Only Setup (Acceptable):**
- Foundation: IP 100%, UA 100%, Browser ID 100%
- ClickID: Server 25%
- High PII: Email 90%
- Medium PII: First Name 95%

## Common Code Patterns by Framework

**Next.js / React:** Pixel is typically initialized in `_app.tsx` or a layout component. CAPI calls are made from API routes (`pages/api/` or `app/api/`). The `_fbc` and `_fbp` cookies can be read server-side from the request headers.

**Django / Flask:** CAPI calls are made from view functions or middleware. `request.META['REMOTE_ADDR']` provides IP, `request.META['HTTP_USER_AGENT']` provides UA, and `request.COOKIES.get('_fbc')` provides the click ID.

**Express.js:** CAPI calls from route handlers. `req.ip` for IP, `req.headers['user-agent']` for UA, `req.cookies._fbc` for click ID (requires `cookie-parser` middleware).

**Shopify Liquid:** Pixel is typically in `theme.liquid`. CAPI is handled by the Shopify Facebook & Instagram app or custom webhooks. Check the data sharing level in the app settings.

**PHP / Laravel:** CAPI calls from controllers. `$_SERVER['REMOTE_ADDR']` for IP, `$_SERVER['HTTP_USER_AGENT']` for UA, `$_COOKIE['_fbc']` for click ID.
