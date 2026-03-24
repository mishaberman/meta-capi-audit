---
name: meta-capi-audit
description: Audits a GitHub repository's source code for Meta Conversions API (CAPI) implementation quality, onboarding status, and Event Match Quality (EMQ) optimization. Clones the repo, scans backend code for CAPI payloads, user data hashing, deduplication logic, and security. Supports multiple CAPI backend methods (Direct HTTP, Meta Business SDK, Parameter Builder Library, Partner Integrations). Produces a scored report with business impact analysis and step-by-step developer action plans for server-side improvements, including actual implementation code using the Parameter Builder Library or pure HTTP calls.
---

# Meta Conversions API (CAPI) Code Audit & Implementation Skill

## Purpose

Analyze a GitHub repository to determine the current implementation status of the Meta Conversions API (server-side). Produce a comprehensive diagnostic report that scores the CAPI setup, evaluates Event Match Quality (EMQ) potential based on user data parameters, checks deduplication logic, and provides file-specific, code-level developer instructions to improve or implement the server-side integration.

This skill supports auditing existing setups AND providing implementation guidance for new setups using pure HTTP calls, the Meta Business SDK, or the CAPI Parameter Builder Library.

*Note: This skill focuses exclusively on CAPI. It does not audit Meta Pixel base code or browser-side event tracking, except to verify that deduplication IDs (`event_id`) are being passed correctly.*

## Input

The advertiser provides:

| Parameter | Required | Description |
|-----------|----------|-------------|
| GitHub Repository | Yes | URL or `owner/repo` format |
| Branch | No | Defaults to main/master |
| Business Type | No | E-commerce, Lead Gen, SaaS, Content — guides event expectations |
| Test Event Code | No | e.g., `TEST12345`. If provided, include it in all generated code snippets. |

Example prompt:
```
Audit my backend code for Meta CAPI setup.
- Repo: mycompany/ecommerce-backend
- Branch: staging
- Test Event Code: TEST84729
```

## Execution Flow

### Phase 1: Repository Acquisition

Clone the repository and identify the backend tech stack:

```bash
gh repo clone <repo_name> /home/ubuntu/repo_to_audit
cd /home/ubuntu/repo_to_audit && git checkout <branch>  # if branch specified
```

Identify the backend tech stack by checking for framework markers. This determines which CAPI SDK patterns to search for:

| Marker File / Pattern | Tech Stack | Expected CAPI Method |
|----------------------|------------|----------------------|
| `package.json` with `express` | Node.js / Express | `facebook-nodejs-business-sdk`, `capi-param-builder`, or `fetch`/`axios` |
| `package.json` with `next` | Next.js API Routes | `facebook-nodejs-business-sdk`, `capi-param-builder`, or `fetch` |
| `requirements.txt` with `django` | Python / Django | `facebook_business` SDK, `capi-param-builder`, or `requests` |
| `composer.json` | PHP / Laravel | `facebook/php-business-sdk`, `capi-param-builder`, or `curl` |
| `Gemfile` with `rails` | Ruby on Rails | `facebookbusiness` SDK, `capi-param-builder`, or `Net::HTTP` |
| `package.json` with `@shopify/shopify-api` | Shopify Custom App | Shopify Webhooks + Direct HTTP API |

### Phase 2: Automated Code Scanning

Run the CAPI-focused audit script to get a structured overview of server-side Meta patterns:

```bash
python3 /home/ubuntu/skills/meta-capi-audit/scripts/capi_audit.py /home/ubuntu/repo_to_audit -o /home/ubuntu/capi_audit_results.json
```

Read `capi_audit_results.json` with the `file` tool. The script returns:

| Field | What It Tells You |
|-------|------------------|
| `capi_status` | Implemented, Partial, or Not Found |
| `capi_method` | Direct HTTP API, Node SDK, Python SDK, Parameter Builder Library, Partner Integration, etc. |
| `detected_server_events` | List of events sent via CAPI |
| `user_data_fields` | Which customer information parameters are collected |
| `has_hashing` | Whether SHA-256 hashing is used for PII |
| `deduplication_status` | Whether `event_id` is included in the payload |
| `security_issues` | Hardcoded access tokens |

### Phase 3: Deep Dive Analysis

Use the `match` tool (`grep` action) and `file` tool (`read` action with line ranges) to inspect the specific backend files identified in Phase 2. Evaluate each dimension:

**3a. CAPI Payload Construction & Backend Method**
- Identify the exact backend method used: Direct HTTP API, Meta Business SDK, Parameter Builder Library, or a Partner Integration (e.g., Shopify, WooCommerce, GTM Server-Side).
- Check the server payload for required fields: `event_name`, `event_time`, `action_source` (must be `"website"` for web events), `event_source_url`, `user_data`.
- Are events sent asynchronously or in batches to avoid blocking the main thread?

**3b. User Data & EMQ Optimization**
- Check `user_data` for Foundation parameters: `client_ip_address` (from request headers, e.g., `req.ip`), `client_user_agent` (from headers), `fbp` (from `_fbp` cookie), `fbc` (from `_fbc` cookie).
- **CRITICAL:** Emphasize the collection of the Click ID (`fbc`). The server should extract it from the `_fbc` cookie or receive it from the frontend.
- Check for High PII: `em` (email) or `ph` (phone).
- Check for Medium PII: `fn`, `ln`, `ct`, `st`, `zp`.
- **CRITICAL:** All PII (`em`, `ph`, `fn`, `ln`, etc.) MUST be SHA-256 hashed. Foundation parameters (`client_ip_address`, `client_user_agent`, `fbc`, `fbp`) MUST NOT be hashed.
- **Invalid Combinations:** Flag if the payload only contains broad combinations like `ct + country + st + zp + ge + client_user_agent` as these will be rejected by Meta.

**3c. Deduplication Logic**
- Does the CAPI payload include `event_id`?
- How is `event_id` generated? (It should ideally be passed from the frontend to ensure it exactly matches the browser pixel's `eventID`).

**3d. Security**
- Is the access token stored securely (environment variable) or hardcoded?
- Is the CAPI call made from a true backend server, or is it exposed in client-side code? (Client-side CAPI is a critical security flaw).

### Phase 4: Scoring

Calculate a CAPI Quality Score (0–100) based on the findings:

```
Start at 100. Deduct points for each gap:

SETUP STATUS
  No CAPI implementation found:                -100 (Stop here)
  CAPI implemented client-side (exposed):      -40

PAYLOAD STRUCTURE
  Missing action_source="website":             -10
  Missing event_source_url:                    -5
  Missing event_time:                          -5

EMQ / USER DATA
  Missing client_ip_address:                   -15 (Critical for IDP)
  Missing client_user_agent:                   -10
  Missing fbp/fbc cookie forwarding:           -10
  No email or phone in user_data:              -15
  No hashing implementation found:             -20 (PII sent in plaintext is rejected)
  No Medium PII (fn, ln, etc.):                -5

DEDUPLICATION
  No event_id in server payload:               -15

SECURITY
  Access token hardcoded in source:            -20

Minimum score: 0
```

**Score Interpretation:**
- **85–100 (Excellent):** Robust server-side setup, high EMQ potential, secure.
- **70–84 (Good):** Solid foundation, missing some user data or deduplication.
- **50–69 (Needs Work):** Significant gaps affecting match quality or deduplication.
- **0–49 (Critical):** Non-functional, insecure, or severely incomplete setup.

### Phase 5: Report Generation

Generate a Markdown report saved to `/home/ubuntu/meta_capi_audit_report.md`. Use the template at `/home/ubuntu/skills/meta-capi-audit/templates/capi_report_template.md` as a structural guide.

**Mandatory Report Sections:**

1. **Executive Summary** — CAPI status, score, 2–3 sentence overview.
2. **CAPI Implementation Status** — Table showing Method, Deduplication, Hashing, and Security.
3. **Server-Side Event Inventory** — List of events sent via CAPI, detailing Custom Data and User Data parameters for each.
4. **EMQ & User Data Analysis** — Table evaluating `client_ip_address`, `client_user_agent`, `fbc`, `fbp`, and PII. Explicitly state the impact of missing fields (e.g., "Missing IP Address breaks Identity Prediction, which yields ~70% match rate").
5. **Click ID (`fbc`) Deep Dive** — Dedicated section emphasizing the importance of `fbc` collection and inclusion in the server payload.
6. **Improvement Opportunities** — Prioritized list (Critical → High → Medium) with business impact.
7. **Developer Action Plan** — Exact file paths, current code, and corrected code snippets for backend fixes. If no CAPI exists, provide full implementation code using the Parameter Builder Library or Direct HTTP API.

### Phase 6: Deliver Report

Use the `message` tool with `type: result`:
1. Attach `/home/ubuntu/meta_capi_audit_report.md`.
2. In the message text, provide a concise summary: CAPI status, score, number of issues by priority, and the single most impactful action to take first.

## Key Rules

**Implementation Guidance:** If the repository has no CAPI implementation, the Developer Action Plan MUST provide complete code to implement it. Recommend the **Parameter Builder Library** (`capi-param-builder`) as the primary method for new setups, as it handles cookie extraction, IP address formatting, and PII hashing automatically.

**Test Event Code:** If the advertiser provides a `test_event_code` (e.g., `TEST12345`), you MUST include it in all generated code snippets in the Developer Action Plan. This allows the advertiser to immediately verify the implementation in the Events Manager Test Events tab.

**Parameter Builder Library (PBL) Workflow:**
When recommending PBL, explain the combined Client + Server workflow:
1. Client loads `clientParamBuilder` and calls `.processAndCollectAllParams` (with `getIpFn` for IPv6).
2. Client passes first-party cookies to the backend.
3. Server calls `builder.processRequest` and sets recommended cookies in response headers.
4. Server calls `getFbc()`, `getFbp()`, `getClientIpAddress()`, and `getNormalizedAndHashedPII()`.
5. Server sends the payload to Meta.

**Hashing:** All PII parameters (`em`, `ph`, `fn`, `ln`, `ge`, `db`, `ct`, `st`, `zp`, `country`) MUST be normalized (lowercase, trim whitespace) and SHA-256 hashed before sending via CAPI. The following MUST NOT be hashed: `client_ip_address`, `client_user_agent`, `fbc`, `fbp`, `external_id`.

**Deduplication:** The server `event_id` must exactly match the browser `eventID`. The recommended method is Event ID + Event Name.

**Access Token Security:** The CAPI access token should NEVER be hardcoded in source code or exposed in client-side bundles. It must be stored in environment variables.

**IP Address:** The `client_ip_address` must be the IP of the *user's browser*, not the IP of the server making the CAPI call. This usually requires extracting it from `req.ip` or the `X-Forwarded-For` header. IPv6 is preferred over IPv4.
