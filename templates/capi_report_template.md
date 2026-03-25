# Meta Conversions API (CAPI) Server-Side Audit Report

**Repository:** `{repo_name}`
**Branch:** `{branch}`
**Analysis Date:** {date}
**Backend Tech Stack:** {tech_stack}
**Test Event Code:** {test_event_code_if_provided}

---

## 1. Executive Summary

**CAPI Setup Status:** {Implemented / Partial / Not Found}

{Write 2–3 sentences summarizing the most important findings regarding the server-side setup: what is working well, what the biggest gap is, and the single most impactful action to take. If CAPI is not found, explicitly state that implementation code is provided below.}

## 2. What's Working Well

*   {Highlight correctly implemented features, e.g., "Deduplication correctly handled on Purchase route"}
*   {Highlight correctly implemented features, e.g., "Email and Phone are properly hashed"}
*   {Highlight correctly implemented features, e.g., "CAPI payload structure is valid"}

## 3. What Needs Improvement

*   {Highlight gaps or errors, e.g., "Missing currency parameter on AddToCart"}
*   {Highlight gaps or errors, e.g., "fbc cookie not extracted"}
*   {Highlight gaps or errors, e.g., "Deduplication missing on non-Purchase events"}

## 4. CAPI Implementation Status

| Dimension | Status | Notes |
|-----------|--------|-------|
| Implementation Method | {Direct HTTP API / Meta Business SDK / None} | {Details; also note if Parameter Builder Library is used as an assist} |
| Deduplication (`event_id`) | {Configured / Not Configured} | {Details} |
| SHA-256 Hashing | {Yes / No / N/A (No PII collected)} | {Which fields} |
| Access Token Security | {Secure / At Risk} | {Env var or hardcoded} |

---

## 5. Server-Side Event Inventory

### Detected CAPI Events

For each event sent from the server, we analyze the Custom Data (e.g., value, currency) and User Data/PII (e.g., email, fbc) included in the payload.

#### Event: {Event Name} (e.g., Purchase)
- **File:** `{file_path}` (Line {line})
- **Custom Data:** `{value, currency, content_ids, etc.}`
- **User Data / PII:** `{client_ip_address, client_user_agent, fbc, fbp, em, etc.}`
- **Issues:** {Any missing required params, especially flag if `fbc` (Click ID) or `client_ip_address` is missing}

*(Repeat the above block for every detected server event. If no events are found, list the recommended events to implement based on the business type.)*

---

## 6. EMQ & User Data Analysis

This section evaluates the customer information parameters sent via CAPI, which directly determine Event Match Quality (EMQ). EMQ scores of 6.0+ are recommended for decreasing CPA, and 5.0+ is the threshold for CAPI Qualified Revenue.

| Category | Parameter | CAPI Field | Found? | File:Line | Impact if Missing |
|----------|-----------|-----------|--------|-----------|------------------|
| Foundation | IP Address | `client_ip_address` | {Yes/No} | {loc} | HIGH priority — critical for identity resolution |
| Foundation | User Agent | `client_user_agent` | {Yes/No} | {loc} | HIGH priority — critical for identity resolution |
| Foundation | Browser ID | `fbp` | {Yes/No} | {loc} | MEDIUM priority — improves cross-session matching |
| Click ID | Click ID | `fbc` | {Yes/No} | {loc} | HIGH priority — one of the strongest matching signals (on par with email) |
| High PII | Email | `em` | {Yes/No} | {loc} | HIGH priority — one of the strongest matching signals |
| High PII | Phone | `ph` | {Yes/No} | {loc} | HIGH priority — one of the strongest matching signals |
| Medium PII | First Name | `fn` | {Yes/No} | {loc} | MEDIUM priority — incremental improvement |
| Medium PII | Last Name | `ln` | {Yes/No} | {loc} | MEDIUM priority — incremental improvement |

---

## 7. Click ID (`fbc`) Deep Dive

The Click ID (`fbc`) is a **HIGH priority** parameter for identity matching, on par with hashed email. It is critical for attributing conversions that originate from Meta ads.

**Current Status:** {Describe how fbc is currently handled on the server, e.g., "Not collected at all", "Read from request cookies", "Passed from frontend payload"}

**Best Practice:** The server should extract the `_fbc` cookie from the incoming HTTP request headers. If the cookie is not present, the frontend should manually parse the `fbclid` query parameter from the URL, construct the `fbc` value (`fb.1.{timestamp}.{fbclid}`), and pass it to the backend.

---

## 8. Improvement Opportunities

### Critical Priority

**{N}. {Issue Title}**

**What's wrong:** {Description of the gap found in the server code.}

**Business impact:** {Explain in terms of EMQ, CPA, attribution, or audience quality. Reference the parameter's priority level per [Meta's Customer Information Parameters documentation](https://developers.facebook.com/docs/marketing-api/conversions-api/parameters/customer-information-parameters).}

**Expected improvement:** {Describe qualitatively: e.g., "Adding hashed email to CAPI is a HIGH priority improvement that can significantly improve EMQ and ad delivery optimization."}

### High Priority

{Same format as above}

### Medium Priority

{Same format as above}

---

## 9. Developer Action Plan

*(If CAPI is not implemented, provide full implementation code using the Parameter Builder Library or Direct HTTP API. If CAPI is implemented, provide the specific fixes needed.)*

### Action 1: {Title}

**Priority:** {Critical / High / Medium}
**Estimated Effort:** {Time estimate}
**Target File(s):** `{file_path}`

**Current Code:**
```javascript
{Paste the actual current code from the repository, or state "None" if new implementation}
```

**Required Update:**
```javascript
{Write the corrected/improved code, or the full implementation code}
```

**Technical Notes:**
{Any important details: hashing requirements, cookie extraction, environment variable setup, Parameter Builder Library workflow, etc.}

---

## 10. Testing & Validation

Once the changes are deployed, validate the setup using these tools:

1. **Test Events Tool:** Go to Events Manager → Data Sources → Settings → Test Events. Include the `test_event_code` {insert code if provided} in your server payload to verify events are received and deduplicated correctly. *(Note: If a PR was generated, a secondary Cleanup PR has also been provided to easily remove this code once validation is complete).*
2. **Payload Helper:** Use the [Payload Helper](https://developers.facebook.com/docs/marketing-api/conversions-api/payload-helper) to validate your JSON structure before sending.
3. **Events Manager:** Monitor the Event Deduplication tab and EMQ scores over the next 7 days. See [Meta's documentation](https://developers.facebook.com/docs/marketing-api/conversions-api/deduplicate-pixel-and-server-events) for current recommended thresholds.

---

## 11. Summary & Next Steps

**Immediate Actions (This Sprint):**
{Top 1–3 actions that will have the biggest impact}
*(If a Pull Request was created, include the link here: "✅ A Pull Request with these fixes has been automatically generated: [Link to PR]")*

**Short-Term (Next 2 Weeks):**
{Additional improvements}

**Ongoing:**
{Monitoring and maintenance recommendations}

---

*Audit generated by Manus Meta CAPI Audit Skill on {date}*
*Note: A significant portion of events can be missed by browser Pixel alone due to ad blockers, iOS privacy changes, and network issues. A fully redundant setup with high EMQ is recommended. See [Meta's CAPI documentation](https://developers.facebook.com/docs/marketing-api/conversions-api) for details.*
