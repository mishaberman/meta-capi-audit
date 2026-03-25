---
name: meta-capi-audit
description: Audits a GitHub repository's source code for Meta Conversions API (CAPI) implementation quality, onboarding status, and Event Match Quality (EMQ) optimization. Clones the repo, scans backend code for CAPI payloads, user data hashing, deduplication logic across all pages, and security. Supports multiple CAPI backend methods (Direct HTTP, Meta Business SDK). Produces a diagnostic report highlighting what's working well and what needs improvement, along with step-by-step developer action plans for server-side fixes, including actual implementation code using the Parameter Builder Library or pure HTTP calls.
---

# Meta Conversions API (CAPI) Code Audit & Implementation Skill

## Purpose

Analyze a GitHub repository to determine the current implementation status of the Meta Conversions API (server-side). Produce a comprehensive diagnostic report that highlights what is currently working well and what needs improvement. The audit evaluates Event Match Quality (EMQ) potential based on user data parameters, verifies deduplication logic across all pages/routes, validates value and currency parameters, and provides file-specific, code-level developer instructions to improve or implement the server-side integration.

This skill supports auditing existing setups AND providing implementation guidance for new setups using pure HTTP calls, the Meta Business SDK, or the CAPI Parameter Builder Library.

*Note: This skill focuses exclusively on CAPI. It does not audit Meta Pixel base code or browser-side event tracking, except to verify that deduplication IDs (`event_id`) are being passed correctly.*

## Input

The advertiser provides:

| Parameter | Required | Description |
|-----------|----------|-------------|
| GitHub Repository | Yes | URL or `owner/repo` format |
| Branch | No | Defaults to main/master |
| Business Type | No | E-commerce, Lead Gen, SaaS, Content — guides event expectations |
| Test Event Code | No | e.g., `TEST12345`. If provided, instantly inject it into the repo's CAPI calls and commit directly. |
| Remove Test Code | No | `true` or `false`. If true, instantly remove any existing test_event_code from the repo and commit directly. |
| Create PR | No | `true` or `false`. If true, automatically create a GitHub Pull Request with the suggested fixes. |

Example prompt:
```
Audit my backend code for Meta CAPI setup.
- Repo: mycompany/ecommerce-backend
- Branch: staging
- Test Event Code: TEST84729
- Create PR: true

Or for instant test code injection/removal (no PR):
```
Inject test event code TEST84729 into mycompany/ecommerce-backend
```
```
Remove the test event code from mycompany/ecommerce-backend
```
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
| `package.json` with `express` | Node.js / Express | `facebook-nodejs-business-sdk` or `fetch`/`axios` to Graph API |
| `package.json` with `next` | Next.js API Routes | `facebook-nodejs-business-sdk` or `fetch` to Graph API |
| `requirements.txt` with `django` | Python / Django | `facebook_business` SDK or `requests` to Graph API |
| `requirements.txt` with `flask`/`fastapi` | Python / Flask / FastAPI | `facebook_business` SDK or `requests` to Graph API |
| `composer.json` | PHP / Laravel | `facebook/php-business-sdk` or `curl` to Graph API |
| `Gemfile` with `rails` | Ruby on Rails | `facebookbusiness` SDK or `Net::HTTP` to Graph API |

Also check if the **Parameter Builder Library** (`capi-param-builder`) is installed as a dependency. This is not a CAPI method itself, but an assist library that handles cookie extraction, IP formatting, and PII hashing for any of the above methods.

### Phase 2: Automated Code Scanning

Run the CAPI-focused audit script to get a structured overview of server-side Meta patterns:

```bash
python3 /home/ubuntu/skills/meta-capi-audit/scripts/capi_audit.py /home/ubuntu/repo_to_audit -o /home/ubuntu/capi_audit_results.json
```

Read `capi_audit_results.json` with the `file` tool. The script returns:

| Field | What It Tells You |
|-------|------------------|
| `capi_status` | Implemented, Partial, or Not Found |
| `capi_method` | Direct HTTP API or Meta Business SDK (Node/Python/PHP/Ruby/Java). Also flags if Parameter Builder Library is used as an assist. |
| `detected_server_events` | List of events sent via CAPI |
| `user_data_fields` | Which customer information parameters are collected |
| `has_hashing` | Whether SHA-256 hashing is used for PII |
| `deduplication_status` | Whether `event_id` is included in the payload |
| `security_issues` | Hardcoded access tokens |
| `has_test_event_code` | Whether a `test_event_code` is present in the CAPI payload code |
| `test_event_code_values` | The actual test code values found (e.g., `TEST12345`) |

### Phase 3: Deep Dive Analysis

Use the `match` tool (`grep` action) and `file` tool (`read` action with line ranges) to inspect the specific backend files identified in Phase 2. Evaluate each dimension:

**3a. CAPI Payload Construction & Backend Method**
- Identify the exact backend method used: **Direct HTTP API** (raw `fetch`/`axios`/`requests`/`curl` calls to `graph.facebook.com`) or **Meta Business SDK** (using typed classes like `EventRequest`, `ServerEvent`, `UserData`). Also note if the Parameter Builder Library is being used as an assist.
- Check the server payload for required fields: `event_name`, `event_time`, `action_source` (must be `"website"` for web events), `event_source_url`, `user_data`.
- **Value & Currency Validation:** For events like `Purchase`, `AddToCart`, or `InitiateCheckout`, verify that `value` and `currency` are correctly populated in the `custom_data` object.
- **Browser vs. Server Payload Comparison:** Check if the custom data parameters sent by the browser pixel (e.g., `fbq('track', 'Purchase', {value: 5, currency: 'USD'})`) match the custom data sent by the server. Flag any mismatches (e.g., browser sends value but server does not, or server sends different content_ids).
- Are events sent asynchronously or in batches to avoid blocking the main thread?

**3b. User Data & EMQ Optimization**
- Check `user_data` for Foundation parameters: `client_ip_address` (from request headers, e.g., `req.ip`), `client_user_agent` (from headers), `fbp` (from `_fbp` cookie), `fbc` (from `_fbc` cookie).
- **CRITICAL:** Emphasize the collection of the Click ID (`fbc`). The server should extract it from the `_fbc` cookie or receive it from the frontend.
- Check for High PII: `em` (email) or `ph` (phone).
- Check for Medium PII: `fn`, `ln`, `ct`, `st`, `zp`.
- **CRITICAL:** If PII (`em`, `ph`, `fn`, `ln`, etc.) is being sent, it MUST be SHA-256 hashed. If no PII is being collected at all, do NOT flag "missing hashing" as an issue — the issue is the missing PII itself. Foundation parameters (`client_ip_address`, `client_user_agent`, `fbc`, `fbp`) MUST NOT be hashed.
- **Invalid Combinations:** Flag if the payload only contains broad combinations like `ct + country + st + zp + ge + client_user_agent` as these will be rejected by Meta.

**3c. Deduplication Logic**
- Does the CAPI payload include `event_id`?
- How is `event_id` generated? (It should ideally be passed from the frontend to ensure it exactly matches the browser pixel's `eventID`).
- **Cross-Page Verification:** Check if deduplication is correctly handled across *all* relevant pages and routes where events are fired, not just a single checkout page.

**3d. Test Event Code Detection**
- Check if a `test_event_code` is present anywhere in the CAPI payload construction. This parameter should ONLY be present during testing and MUST be removed before production deployment.
- If found, flag it as a **CRITICAL** issue in the "What Needs Improvement" section. A leftover test code causes all events to be routed to the Test Events tab in Events Manager instead of being processed for ad delivery and attribution.
- Report the exact file, line number, and the test code value found.

**3e. Security**
- Is the access token stored securely (environment variable) or hardcoded?
- Is the CAPI call made from a true backend server, or is it exposed in client-side code? (Client-side CAPI is a critical security flaw).

### Phase 4: Report Generation

Generate a Markdown report saved to `/home/ubuntu/meta_capi_audit_report.md`. Use the template at `/home/ubuntu/skills/meta-capi-audit/templates/capi_report_template.md` as a structural guide.

**Mandatory Report Sections:**

1. **Executive Summary** — CAPI status, 2–3 sentence overview of the setup.
2. **What's Working Well** — Bulleted list of correctly implemented features (e.g., "Deduplication correctly handled on Purchase route", "Email and Phone are properly hashed").
3. **What Needs Improvement** — Bulleted list of gaps or errors (e.g., "Missing currency parameter on AddToCart", "fbc cookie not extracted").
4. **CAPI Implementation Status** — Table showing Method, Deduplication, Hashing, and Security.
5. **Server-Side Event Inventory** — List of events sent via CAPI, detailing Custom Data (including value/currency checks) and User Data parameters for each.
6. **EMQ & User Data Analysis** — Table evaluating `client_ip_address`, `client_user_agent`, `fbc`, `fbp`, and PII. State the priority level and impact of each missing field, referencing [Meta's Customer Information Parameters documentation](https://developers.facebook.com/docs/marketing-api/conversions-api/parameters/customer-information-parameters).
7. **Click ID (`fbc`) Deep Dive** — Dedicated section emphasizing the importance of `fbc` collection and inclusion in the server payload.
8. **Developer Action Plan** — Exact file paths, current code, and corrected code snippets for backend fixes. If no CAPI exists, provide full implementation code using the Parameter Builder Library or Direct HTTP API.

### Phase 5: Interactive Fix Review & Pull Request Creation

Instead of automatically creating a PR, use an interactive workflow to ensure the advertiser controls the changes:

1. **Deliver the Report First:** Use the `message` tool (`type: ask`) to deliver the audit report (`/home/ubuntu/meta_capi_audit_report.md`) and summarize the findings.
2. **Ask for Permission:** In the same message, ask the user: *"Would you like me to automatically apply these fixes and create a Pull Request for you to review?"*
3. **If Accepted:**
   - Create a new branch: `git checkout -b fix/meta-capi-optimization`
   - Apply the exact code changes outlined in the Developer Action Plan.
   - **Make granular, logical commits** for each specific fix (e.g., `fix(capi): add event_id deduplication`, `feat(capi): add SHA-256 hashing`).
   - Push the branch and create the PR using `gh pr create` with a detailed body (including before/after diffs).
   - Send a message with the PR link and ask: *"The PR is ready for your review. Once you merge it, would you like me to inject a `test_event_code` so you can verify the events in Events Manager?"*
4. **If Rejected / Manual:** Acknowledge their choice and offer to help if they have questions while implementing the fixes manually.

### Phase 6: Interactive Test Event Code Injection / Removal

If the user agrees to inject a test event code (either after merging the PR, or as a standalone request):
1. **Ask for the Code:** If they haven't provided one, ask: *"What test event code should I use? (e.g., TEST12345)"*
2. **Inject:** Find the CAPI payload construction and inject `test_event_code: '<CODE>'` at the top level.
3. **Commit & Push Directly:** Do NOT create a PR for this temporary testing step. Commit directly to the current deployment branch:
   - `git commit -am "chore(capi): inject test_event_code for validation"`
   - `git push origin <branch>`
4. **Wait for Validation:** Tell the user: *"The test code is live. Please trigger some events on your site and check the Events Manager Test Events tab. Let me know when you're done, and I will remove the test code."*
5. **Remove:** Once they confirm, strip the `test_event_code`, commit (`chore(capi): remove test_event_code`), and push directly.

## Key Rules

**Implementation Guidance:** If the repository has no CAPI implementation, the Developer Action Plan MUST provide complete code to implement it. Recommend the **Parameter Builder Library** (`capi-param-builder`) as the primary method for new setups, as it handles cookie extraction, IP address formatting, and PII hashing automatically.

**Test Event Code Detection:** The audit MUST check for any active `test_event_code` in the CAPI payload code. A leftover test code in production is a **CRITICAL** issue because it routes all events to the Test Events tab in Events Manager, meaning they are NOT processed for ad delivery, attribution, or optimization. If found, it MUST appear as the first item in "What Needs Improvement" and the first action in the Developer Action Plan.

**Test Event Code Injection:** If the advertiser provides a `test_event_code` (e.g., `TEST12345`), you MUST include it in all generated code snippets in the Developer Action Plan. If they ask to inject it directly, modify the repo files and push the commit immediately without a PR.

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
