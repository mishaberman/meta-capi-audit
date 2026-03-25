# Meta CAPI Audit — Output Outline

This file defines the structure and content of the audit report produced by the meta-capi-audit skill. Edit this file to control what appears in the final output, reorder sections, or add/remove content areas.

---

## Report Header

| Field | Description |
|-------|-------------|
| Repository | The GitHub repo that was audited |
| Branch | The branch scanned (defaults to main/master) |
| Analysis Date | Date the audit was run |
| Backend Tech Stack | Detected frameworks (e.g., Express.js, Django, Next.js) |

---

## Section 1: Executive Summary

**Purpose:** Give the reader a 2–3 sentence snapshot of the entire audit.

**Contents:**
- CAPI Setup Status: **Implemented** / **Partial** / **Not Found**
- One sentence on what is working well
- One sentence on the single biggest gap
- One sentence on the most impactful action to take

---

## Section 2: What's Working Well

**Purpose:** Highlight everything the developer got right so they know what NOT to change.

**Format:** Bulleted list. Each bullet is a specific, concrete finding.

**Example items:**
- Deduplication (`event_id`) correctly handled on Purchase route
- Email and phone are properly SHA-256 hashed before sending
- Access token stored securely in environment variables
- `client_ip_address` and `client_user_agent` correctly extracted from request headers

---

## Section 3: What Needs Improvement

**Purpose:** Highlight every gap, error, or missing element — ordered by severity.

**Format:** Bulleted list. Each bullet is a specific finding with file/line when possible.

**Severity ordering:**
1. CRITICAL items first (e.g., leftover `test_event_code`, hardcoded access token)
2. HIGH priority items next (e.g., missing `fbc`, missing deduplication)
3. MEDIUM priority items last (e.g., missing `fn`/`ln`)

**Example items:**
- **CRITICAL:** Active `test_event_code` (`TEST84729`) found in `server/capi.js:42` — must be removed before production
- Missing `fbc` (Click ID) — not extracted from `_fbc` cookie
- Deduplication missing on AddToCart and ViewContent routes
- `currency` parameter missing on AddToCart event

---

## Section 4: CAPI Implementation Status

**Purpose:** One-glance table showing the overall health of the CAPI setup.

**Format:** Table with 3 columns: Dimension, Status, Notes.

**Rows:**

| Dimension | Possible Values | What to Show in Notes |
|-----------|----------------|----------------------|
| Implementation Method | Direct HTTP API / Meta Business SDK / None | Which SDK or HTTP library; whether Parameter Builder Library is also used |
| Deduplication (`event_id`) | Configured / Not Configured | How `event_id` is generated; whether it matches browser `eventID` |
| SHA-256 Hashing | Yes / No / N/A (no PII collected) | Which fields are hashed; flag if PII is sent unhashed |
| Access Token Security | Secure / At Risk | Env var vs. hardcoded; flag if token appears in client-side code |
| Test Event Code | Not Present / **ACTIVE — REMOVE** | If active: the value, file, and line number |

---

## Section 5: Server-Side Event Inventory

**Purpose:** Per-event breakdown of what the server is actually sending to Meta.

**Format:** One block per detected event (e.g., Purchase, AddToCart, ViewContent, Lead).

**Each event block contains:**

| Field | Description |
|-------|-------------|
| Event Name | e.g., `Purchase` |
| File & Line | Where the event is constructed in the codebase |
| Browser Custom Data | Parameters from the `fbq('track')` call (value, currency, content_ids, etc.) |
| Server Custom Data | Parameters from the CAPI payload (value, currency, content_ids, etc.) |
| Browser vs. Server Match? | Flag mismatches (e.g., browser sends `content_ids` but server does not) |
| User Data / PII | Which user_data fields are included (client_ip, user_agent, fbc, fbp, em, ph, etc.) |
| Issues | Missing required params, missing fbc, value/currency gaps, payload mismatches |

**If no events found:** List the recommended events to implement based on the business type.

---

## Section 6: EMQ & User Data Analysis

**Purpose:** Evaluate which customer information parameters are being sent, and their impact on Event Match Quality.

**Format:** Table with columns: Category, Parameter, CAPI Field, Found?, File:Line, Impact if Missing.

**Parameters to evaluate (in order):**

| Category | Parameter | CAPI Field | Priority |
|----------|-----------|-----------|----------|
| Foundation | IP Address | `client_ip_address` | HIGH |
| Foundation | User Agent | `client_user_agent` | HIGH |
| Foundation | Browser ID | `fbp` | MEDIUM |
| Click ID | Click ID | `fbc` | HIGH |
| High PII | Email | `em` | HIGH |
| High PII | Phone | `ph` | HIGH |
| Medium PII | First Name | `fn` | MEDIUM |
| Medium PII | Last Name | `ln` | MEDIUM |

**Rules:**
- Only flag "missing hashing" if PII is actually being collected but sent unhashed
- If no PII is collected at all, the issue is "missing PII" not "missing hashing"
- Foundation parameters (`client_ip_address`, `client_user_agent`, `fbc`, `fbp`) must NOT be hashed

---

## Section 7: Click ID (`fbc`) Deep Dive

**Purpose:** Dedicated section emphasizing `fbc` as a HIGH priority signal on par with email.

**Contents:**
- Current status: How `fbc` is handled today (not collected / read from cookies / passed from frontend)
- Best practice: Extract `_fbc` cookie from request headers; fallback to constructing from `fbclid` URL parameter
- Code example showing the correct extraction pattern for the detected tech stack

---

## Section 8: Improvement Opportunities

**Purpose:** Detailed write-up of each issue found, grouped by priority tier.

**Format:** Grouped under Critical / High / Medium headings. Each item has:

| Field | Description |
|-------|-------------|
| Issue Title | Short name (e.g., "Remove leftover test_event_code") |
| What's wrong | Description of the gap found in the code |
| Business impact | Impact on EMQ, CPA, attribution, or audience quality — reference Meta docs, no specific % claims |
| Expected improvement | Qualitative description of what fixing this will achieve |

---

## Section 9: Developer Action Plan

**Purpose:** Copy-paste-ready code fixes that a developer can implement immediately.

**Format:** One action block per fix, ordered by priority.

**Each action block contains:**

| Field | Description |
|-------|-------------|
| Title | Short name (e.g., "Add event_id deduplication") |
| Priority | Critical / High / Medium |
| Estimated Effort | Time estimate (e.g., "30 minutes") |
| Target File(s) | Exact file path(s) in the repo |
| Current Code | The actual code from the repo today (or "None" for new implementations) |
| Required Update | The corrected/improved code |
| Technical Notes | Hashing requirements, cookie extraction details, env var setup, etc. |

**If CAPI is not implemented at all:** Provide full implementation code using the Parameter Builder Library or Direct HTTP API.

---

## Section 10: Testing & Validation

**Purpose:** Tell the developer how to verify the changes work.

**Contents:**
1. **Test Events Tool** — How to use Events Manager Test Events tab with `test_event_code`
2. **Payload Helper** — Link to Meta's Payload Helper for JSON validation
3. **Events Manager** — What to monitor (deduplication tab, EMQ scores) over the next 7 days

---

## Section 11: Summary & Next Steps

**Purpose:** Prioritized action plan with timeframes.

**Format:**

| Timeframe | Contents |
|-----------|----------|
| Immediate (This Sprint) | Top 1–3 highest-impact actions; PR link if one was created |
| Short-Term (Next 2 Weeks) | Additional improvements |
| Ongoing | Monitoring and maintenance recommendations |

---

## Interactive Outputs (Beyond the Report)

In addition to the written report, the skill produces these interactive outputs during the conversation:

### Decision Point 1: Fix Application
After delivering the report, the skill asks:
> "Would you like me to automatically apply these fixes and create a Pull Request for you to review?"

- **If yes** → Creates branch, applies fixes with granular commits, opens PR, shares link
- **If no** → Acknowledges and offers to help with manual implementation questions

### Decision Point 2: Test Event Code Injection
After the PR is created (or merged), the skill asks:
> "Would you like me to inject a test_event_code so you can verify the events in Events Manager?"

- **If yes** → Asks for the code (if not provided), injects it, commits directly to branch
- **If no** → Provides manual instructions for adding test code

### Decision Point 3: Test Code Cleanup
After the user confirms testing is complete, the skill asks:
> "Ready to remove the test code?"

- Strips `test_event_code` from all CAPI payloads, commits directly

---

## Notes for Editing This Outline

- **To remove a section:** Delete the section block. Update the SKILL.md Phase 4 "Mandatory Report Sections" list to match.
- **To reorder sections:** Move the blocks and renumber. Update the report template (`templates/capi_report_template.md`) to match.
- **To add a section:** Add a new block here, then add corresponding content to the report template and update SKILL.md Phase 4.
- **To change what's checked:** Edit the parameters/rules within each section. The scanner patterns in `scripts/capi_audit.py` may also need updating for new detection logic.
