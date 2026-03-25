# Meta Conversions API (CAPI) Audit Skill

**meta-capi-audit** is an autonomous AI skill that audits, scores, and fixes Meta Conversions API (CAPI) implementations directly from an advertiser's GitHub repository. It acts as an expert Meta Solutions Engineer — scanning the entire codebase to evaluate server-side tracking quality, Event Match Quality (EMQ) potential, deduplication logic, and security posture. It produces a scored diagnostic report with exact code-level fixes, and can automatically submit a Pull Request with the corrections applied.

This skill focuses exclusively on **direct CAPI integrations** (Direct HTTP API and Meta Business SDK). Partner integrations such as Shopify, WooCommerce, and GTM Server-Side are out of scope.

---

## Inputs

| Parameter | Required | Description |
|-----------|----------|-------------|
| GitHub Repository | Yes | URL or `owner/repo` format |
| Branch | No | Defaults to `main` or `master` |
| Business Type | No | E-commerce, Lead Gen, SaaS, or Content — guides expected event coverage |
| Test Event Code | No | e.g., `TEST12345`. Woven into all generated code so events appear in Events Manager's Test Events tab. |
| Create PR | No | If `true`, the skill creates a GitHub Pull Request with granular commits for each fix. |

**Example prompt:**
```
Audit my backend code for Meta CAPI setup.
- Repo: mycompany/ecommerce-backend
- Branch: staging
- Test Event Code: TEST84729
- Create PR: true
```

---

## What It Does

### 1. Multi-Framework Code Scanning

The skill clones the repository and auto-detects the backend tech stack by inspecting dependency files (`package.json`, `requirements.txt`, `composer.json`, `Gemfile`). It supports Node.js/Express, Next.js, Django, Flask, FastAPI, PHP/Laravel, and Ruby on Rails.

It then runs a specialized Python scanner with 50+ regex patterns to detect the two primary CAPI integration methods:

| CAPI Method | What It Detects |
|-------------|-----------------|
| **Direct HTTP API** | Raw `fetch`, `axios`, `requests`, or `curl` calls to `graph.facebook.com/v{version}/{pixel_id}/events` |
| **Meta Business SDK** | Official SDK imports and typed classes — `facebook-nodejs-business-sdk` (Node.js), `facebook_business` (Python), `facebook/php-business-sdk` (PHP), `facebookbusiness` (Ruby) — including `EventRequest`, `ServerEvent`, `UserData`, and `CustomData` |

The scanner also flags whether the **Parameter Builder Library** (`capi-param-builder`) is installed as a dependency. This is not a CAPI method itself, but an assist library that handles cookie extraction, IP address formatting (IPv6 preferred), and PII normalization/hashing automatically.

### 2. Deep Dive Analysis and Scoring

After the automated scan, the skill performs a manual deep dive into the flagged files and evaluates five dimensions:

**Payload Structure** — Checks for required fields (`event_name`, `event_time`, `action_source`, `event_source_url`) and whether events are sent asynchronously to avoid blocking the main thread.

**EMQ and User Data** — Evaluates Foundation parameters (`client_ip_address`, `client_user_agent`, `fbc`, `fbp`), High PII (`em`, `ph`), and Medium PII (`fn`, `ln`, `ct`, `st`, `zp`). Each missing parameter is mapped to its priority level and impact on event matching, referencing [Meta's Customer Information Parameters documentation](https://developers.facebook.com/docs/marketing-api/conversions-api/parameters/customer-information-parameters).

**Hashing** — Verifies that all PII parameters are SHA-256 hashed after normalization (lowercase, trim whitespace), and that Foundation parameters (`client_ip_address`, `client_user_agent`, `fbc`, `fbp`) are explicitly NOT hashed.

**Deduplication** — Checks whether `event_id` is included in the CAPI payload and whether it matches the browser pixel's `eventID` for proper deduplication within the 48-hour window.

**Security** — Flags hardcoded access tokens in source code and detects if CAPI calls are being made from client-side code (which exposes the token and defeats the purpose of server-side tracking).

The findings are scored on a **0–100 scale**:

| Score | Rating | Meaning |
|-------|--------|---------|
| 85–100 | Excellent | Robust server-side setup, high EMQ potential, secure |
| 70–84 | Good | Solid foundation, missing some user data or deduplication |
| 50–69 | Needs Work | Significant gaps affecting match quality or deduplication |
| 0–49 | Critical | Non-functional, insecure, or severely incomplete setup |

### 3. Per-Event Reporting

The report includes a detailed breakdown for every detected event, showing two separate tables per event:

**Custom Data** — Parameters like `value`, `currency`, `content_ids`, `content_type`, `num_items`, and `content_name` for both browser-side and server-side.

**User Data / PII** — Parameters like `em`, `ph`, `fn`, `ln`, `fbc`, `fbp`, `client_ip_address`, and `client_user_agent` for both browser-side and server-side. This makes it immediately clear which user data is being sent where, and what gaps exist.

The report also includes a dedicated **Click ID (`fbc`) Deep Dive** section that emphasizes the importance of collecting the `fbc` parameter. The `fbc` value is one of the highest-priority matching signals and is considered on par with email. The section covers both cookie-based extraction (`_fbc` cookie) and the `fbclid` URL parameter fallback, including the exact format for constructing the `fbc` value: `fb.1.{timestamp}.{fbclid}`.

### 4. Automated Pull Request Creation

When `Create PR: true` is specified, the skill goes beyond reporting and actually applies the fixes to the code:

1. Creates a new branch (`fix/meta-capi-optimization`) from the target branch.
2. Applies the exact code changes from the Developer Action Plan to the repository files.
3. Makes **granular, logical commits** for each specific fix — not one giant commit. Examples:
   - `fix(capi): add event_id deduplication to frontend and backend`
   - `feat(capi): add SHA-256 hashing for email and phone parameters`
   - `fix(capi): correct spelling of action_source parameter`
   - `feat(capi): extract and forward _fbc and _fbp cookies`
4. Generates a detailed **PR body** that includes a summary of why the changes improve the integration, a bulleted list of every modification, and **Before/After code diffs** for the most critical changes.
5. Submits the PR via the GitHub CLI and includes the link in the final delivery.

### 5. Implementation Guidance for New Setups

If the repository has no existing CAPI implementation, the skill provides complete, copy-pasteable implementation code rather than just flagging the gap. It recommends the **Parameter Builder Library** as the primary assist for new setups, providing the full Client + Server workflow:

1. Client loads `clientParamBuilder` and calls `.processAndCollectAllParams` (with `getIpFn` for IPv6).
2. Client passes first-party cookies to the backend.
3. Server calls `builder.processRequest` and sets recommended cookies in response headers.
4. Server calls `getFbc()`, `getFbp()`, `getClientIpAddress()`, and `getNormalizedAndHashedPII()`.
5. Server sends the payload to Meta via Direct HTTP API or Meta Business SDK.

For setups that prefer not to use the Parameter Builder Library, the skill provides equivalent code using pure HTTP calls with manual hashing and cookie extraction.

### 6. Live Testing Support

When a `Test Event Code` is provided (e.g., `TEST12345`), the skill weaves it into every generated code snippet and PR. The `test_event_code` parameter is placed at the top level of the CAPI payload alongside `data` and `access_token`, so events appear in the Events Manager Test Events tab within 30 seconds of deployment. 

If `Create PR: true` was requested, the skill automatically generates a **secondary Cleanup PR** that removes the `test_event_code` from the codebase. The advertiser can merge the main PR, validate the events in Events Manager, and then immediately merge the Cleanup PR to safely remove the test code before going to production.

---

## Outputs

| Output | Format | Description |
|--------|--------|-------------|
| Diagnostic Report | Markdown file (`meta_capi_audit_report.md`) | Full audit with score, per-event breakdowns, EMQ analysis, and developer action plan |
| Pull Request | GitHub PR link | Granular commits with before/after diffs and structured changelog (if `Create PR: true`) |
| Implementation Code | Embedded in report | Complete code using Parameter Builder Library or Direct HTTP API (if no CAPI exists) |

---

## Skill Files

| File | Purpose |
|------|---------|
| `SKILL.md` | Execution instructions, scoring rubric, and key rules for the AI agent |
| `scripts/capi_audit.py` | Automated Python scanner with 50+ regex patterns for CAPI detection |
| `templates/capi_report_template.md` | Structural template for the Markdown audit report |
| `references/capi_best_practices.md` | EMQ parameter categories, hashing rules, deduplication logic, and framework-specific code patterns |
