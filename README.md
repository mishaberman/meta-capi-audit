# Meta Conversions API (CAPI) Audit Skill

**meta-capi-audit** is an autonomous AI skill designed to audit, score, and fix Meta Conversions API (CAPI) implementations directly from an advertiser's GitHub repository. 

It acts as an expert Meta Solutions Engineer, scanning the entire codebase to evaluate server-side tracking quality, Event Match Quality (EMQ) potential, and deduplication logic. It doesn't just tell you what's wrong—it provides the exact code to fix it, and can even automatically generate a Pull Request with the corrections.

## What It Does

### 1. Multi-Framework Code Scanning
The skill clones the repository and automatically detects the backend tech stack (Node/Express, Next.js, Django, Flask, PHP/Laravel, Rails, Shopify, etc.). It runs a specialized scanner with 50+ regex patterns to detect:
- **CAPI Endpoints:** Direct HTTP API calls to `graph.facebook.com`
- **SDK Usage:** Meta Business SDKs (`facebook-nodejs-business-sdk`, `facebook_business`, etc.)
- **Parameter Builder Library:** Detection of `capi-param-builder` workflows
- **Partner Integrations:** Shopify, WooCommerce, and GTM Server-Side connectors

### 2. Deep Dive Analysis & Scoring
It evaluates the implementation against Meta's best practices and calculates a **CAPI Quality Score (0–100)** based on:
- **Payload Structure:** Are required fields (`event_name`, `event_time`, `action_source`, `event_source_url`) present?
- **EMQ & User Data:** Are Foundation parameters (`client_ip_address`, `client_user_agent`, `fbc`, `fbp`) collected correctly? Are High/Medium PII fields included?
- **Hashing:** Is SHA-256 hashing correctly applied to PII (and *not* applied to Foundation parameters)?
- **Deduplication:** Is `event_id` generated and passed correctly to align with the browser pixel?
- **Security:** Are access tokens stored securely in environment variables, or dangerously exposed in client-side code?

### 3. Actionable Reporting
The skill generates a comprehensive Markdown report containing:
- An Executive Summary and Quality Score
- A per-event breakdown showing Custom Data and User Data/PII for both browser and server sides
- An EMQ analysis table detailing the specific impact of missing parameters (e.g., "Missing IP Address breaks Identity Prediction, which yields ~70% match rate")
- A deep dive into Click ID (`fbc`) collection
- A prioritized Developer Action Plan with exact file paths, current code, and corrected code snippets

### 4. Automated Pull Request Creation
If requested (`Create PR: true`), the skill goes beyond reporting and actually fixes the code:
- It creates a new branch (`fix/meta-capi-optimization`).
- It applies the exact code changes to the repository files (adding deduplication, fixing parameter spelling, adding missing PII, applying hashing).
- It makes **granular, developer-friendly commits** for each specific fix (e.g., `fix(capi): add event_id deduplication`).
- It submits a Pull Request with a detailed PR body showing before/after code diffs, so the reviewing developer knows exactly what changed and why.

### 5. Implementation Guidance for New Setups
If the repository has no existing CAPI implementation, the skill doesn't just fail—it provides complete, copy-pasteable implementation code. It defaults to recommending the **Parameter Builder Library** (`capi-param-builder`) as the primary method for new setups, providing the full Client + Server workflow.

### 6. Live Testing Support
Advertisers can provide a `Test Event Code` (e.g., `TEST12345`) as an input parameter. The skill will automatically weave this code into all generated code snippets and PRs, allowing the advertiser to immediately verify the events in the Events Manager Test Events tab within 30 seconds of deployment.

## How to Use It

Provide the skill with the GitHub repository URL and optional parameters:

```text
Audit my backend code for Meta CAPI setup.
- Repo: mycompany/ecommerce-backend
- Branch: staging
- Test Event Code: TEST84729
- Create PR: true
```

## Output Examples

- **Diagnostic Report:** A detailed Markdown file (`meta_capi_audit_report.md`) attached to the final message.
- **Pull Request:** A link to a GitHub PR containing granular commits and a detailed changelog.
- **Implementation Code:** Full code snippets using the Parameter Builder Library or Direct HTTP API if no setup exists.
