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

### Phase 3: Deep Dive Analysis

Use the `match` tool (`grep` action) and `file` tool (`read` action with line ranges) to inspect the specific backend files identified in Phase 2. Evaluate each dimension:

**3a. CAPI Payload Construction & Backend Method**
- Identify the exact backend method used: **Direct HTTP API** (raw `fetch`/`axios`/`requests`/`curl` calls to `graph.facebook.com`) or **Meta Business SDK** (using typed classes like `EventRequest`, `ServerEvent`, `UserData`). Also note if the Parameter Builder Library is being used as an assist.
- Check the server payload for required fields: `event_name`, `event_time`, `action_source` (must be `"website"` for web events), `event_source_url`, `user_data`.
- **Value & Currency Validation:** For events like `Purchase`, `AddToCart`, or `InitiateCheckout`, verify that `value` and `currency` are correctly populated in the `custom_data` object.
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

**3d. Security**
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

### Phase 5: Pull Request Creation (If Requested)

If the advertiser requested `Create PR: true`:
1. Create a new branch from the target branch: `git checkout -b fix/meta-capi-optimization`
2. Apply the exact code changes outlined in the Developer Action Plan directly to the files in `/home/ubuntu/repo_to_audit`.
3. **Make granular, logical commits** for each specific fix (do NOT make one giant commit). For example:
   - `git commit -m "fix(capi): add event_id deduplication to frontend and backend"`
   - `git commit -m "feat(capi): add SHA-256 hashing for email and phone parameters"`
   - `git commit -m "fix(capi): correct spelling of action_source parameter"`
   - `git commit -m "feat(capi): extract and forward _fbc and _fbp cookies"`
4. Push the branch to the remote repository.
5. **Generate a detailed PR Body:** Create a file at `/home/ubuntu/pr_body.md` that explicitly details the changes made. It MUST include:
   - A summary of why these changes improve the CAPI integration (e.g., EMQ improvement, deduplication fix).
   - A "Changes Made" section with a bulleted list of exactly what was modified.
   - A "File Diffs" section showing the **Before** and **After** code snippets for the most critical changes, so the reviewer can understand the exact logic applied without having to dig through the GitHub diff view.
6. Create the PR using the GitHub CLI: `gh pr create --title "Optimize Meta CAPI Implementation" --body-file /home/ubuntu/pr_body.md`
7. Note the PR URL to include in the final delivery.

### Phase 6: Instant Test Event Code Injection / Removal

If the advertiser requests to inject or remove a test event code directly (without a full audit or PR):
1. **Inject:** If `Test Event Code` is provided, find the CAPI payload construction in the code and inject `test_event_code: '<CODE>'` at the top level (alongside `data` and `access_token`).
2. **Remove:** If `Remove Test Code: true` is requested, find and remove the `test_event_code` parameter from the codebase.
3. **Commit & Push Directly:** Do NOT create a PR. Commit directly to the current branch:
   - `git commit -am "chore(capi): inject test_event_code for validation"`
   - `git commit -am "chore(capi): remove test_event_code after validation"`
   - `git push origin <branch>`
4. Inform the advertiser that the code has been pushed and is ready for immediate testing/deployment.

### Phase 7: Deliver Report

Use the `message` tool with `type: result`:
1. Attach `/home/ubuntu/meta_capi_audit_report.md`.
2. In the message text, provide a concise summary: CAPI status, what's working well, what needs improvement, and the single most impactful action to take first.
3. If PRs were created, prominently include the links to both the main Optimization PR and the Cleanup PR (if applicable).

## Key Rules

**Implementation Guidance:** If the repository has no CAPI implementation, the Developer Action Plan MUST provide complete code to implement it. Recommend the **Parameter Builder Library** (`capi-param-builder`) as the primary method for new setups, as it handles cookie extraction, IP address formatting, and PII hashing automatically.

**Test Event Code:** If the advertiser provides a `test_event_code` (e.g., `TEST12345`), you MUST include it in all generated code snippets in the Developer Action Plan. If they ask to inject it directly, modify the repo files and push the commit immediately without a PR.

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
