#!/usr/bin/env python3
"""
Meta Conversions API (CAPI) Repository Audit Scanner
Scans a codebase specifically for server-side Meta CAPI implementation patterns.
Outputs a structured JSON with findings, detected events, and quality indicators.
"""
import os
import re
import json
import argparse
from pathlib import Path
from collections import defaultdict

# ---------------------------------------------------------------------------
# Pattern Definitions
# ---------------------------------------------------------------------------

CAPI_PATTERNS = {
    "endpoint": [
        (r"graph\.facebook\.com/v[\d.]+/\d+/events", "Direct CAPI endpoint"),
        (r"graph\.facebook\.com/v[\d.]+/[^/]+/events", "CAPI endpoint (variable pixel ID)"),
        (r"graph\.facebook\.com.*/events", "CAPI endpoint (generic)"),
    ],
    "sdk_python": [
        (r"from\s+facebook_business", "Python SDK import"),
        (r"FacebookAdsApi", "Python SDK API class"),
        (r"from\s+facebook_business\.adobjects\.server_event\s+import", "Python ServerEvent import"),
    ],
    "sdk_node": [
        (r"require\s*\(\s*['\"]facebook-nodejs-business-sdk['\"]\s*\)", "Node.js SDK require"),
        (r"from\s+['\"]facebook-nodejs-business-sdk['\"]", "Node.js SDK import"),
        (r"bizSdk", "Node.js SDK reference"),
    ],
    "sdk_php": [
        (r"use\s+FacebookAds\\", "PHP SDK use statement"),
        (r"FacebookAds\\Api", "PHP SDK API class"),
    ],
    "sdk_ruby": [
        (r"require\s+['\"]facebookbusiness['\"]", "Ruby SDK require"),
        (r"FacebookAds::ServerEvent", "Ruby SDK ServerEvent"),
    ],
    "sdk_classes": [
        (r"EventRequest", "EventRequest class usage"),
        (r"ServerEvent", "ServerEvent class usage"),
        (r"UserData", "UserData class usage"),
        (r"CustomData", "CustomData class usage"),
    ],
    "payload_required": [
        (r"['\"]?event_name['\"]?\s*[:=]", "event_name field"),
        (r"['\"]?event_time['\"]?\s*[:=]", "event_time field"),
        (r"['\"]?action_source['\"]?\s*[:=]\s*['\"]website['\"]", "action_source = website"),
        (r"['\"]?event_source_url['\"]?\s*[:=]", "event_source_url field"),
    ],
    "payload_user_data": [
        (r"['\"]?client_ip_address['\"]?\s*[:=]", "client_ip_address"),
        (r"['\"]?client_user_agent['\"]?\s*[:=]", "client_user_agent"),
        (r"['\"]?(?:user_data\s*[\[{].*)?['\"]?em['\"]?\s*[:=]", "email (em)"),
        (r"['\"]?(?:user_data\s*[\[{].*)?['\"]?ph['\"]?\s*[:=]", "phone (ph)"),
        (r"['\"]?(?:user_data\s*[\[{].*)?['\"]?fn['\"]?\s*[:=]", "first name (fn)"),
        (r"['\"]?(?:user_data\s*[\[{].*)?['\"]?ln['\"]?\s*[:=]", "last name (ln)"),
        (r"['\"]?fbc['\"]?\s*[:=]", "click ID (fbc)"),
        (r"['\"]?fbp['\"]?\s*[:=]", "browser ID (fbp)"),
        (r"['\"]?external_id['\"]?\s*[:=]", "external ID"),
    ],
    "dedup_server": [
        (r"['\"]?event_id['\"]?\s*[:=]\s*([^,}\s]+)", "Server-side event_id"),
    ],
}

HASHING_PATTERNS = [
    (r"sha256", "SHA-256 reference"),
    (r"createHash\s*\(\s*['\"]sha256['\"]\s*\)", "Node.js SHA-256 hash"),
    (r"hashlib\.sha256", "Python SHA-256 hash"),
    (r"hash\s*\(\s*['\"]sha256['\"]", "PHP SHA-256 hash"),
    (r"Digest::SHA256", "Ruby SHA-256 hash"),
    (r"MessageDigest\.getInstance\s*\(\s*['\"]SHA-256['\"]", "Java SHA-256 hash"),
    (r"crypto\.subtle\.digest\s*\(\s*['\"]SHA-256['\"]", "Web Crypto SHA-256"),
]

SECURITY_PATTERNS = [
    (r"access_token\s*[:=]\s*['\"][A-Za-z0-9]{20,}['\"]", "Hardcoded access token"),
    (r"EAAG[A-Za-z0-9]+", "Facebook access token pattern in source"),
]

COOKIE_PATTERNS = [
    (r"_fbc", "fbc cookie reference"),
    (r"_fbp", "fbp cookie reference"),
    (r"req(?:uest)?\.cookies.*_fb[cp]", "Server-side cookie extraction"),
    (r"\$_COOKIE\['?_fb[cp]'", "PHP cookie extraction"),
    (r"request\.COOKIES\.get\('?_fb[cp]'", "Python/Django cookie extraction"),
]

# ---------------------------------------------------------------------------
# File Filtering
# ---------------------------------------------------------------------------

CODE_EXTENSIONS = {
    '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs',
    '.py', '.php', '.rb', '.java', '.go', '.rs', '.cs',
    '.yaml', '.yml', '.json', '.env', '.toml', '.ini', '.cfg',
}

IGNORE_DIRS = {
    'node_modules', 'vendor', '.git', 'dist', 'build', 'out', '.next',
    '__pycache__', '.cache', 'coverage', '.nyc_output', 'tmp', 'temp',
    'public/assets', 'static/vendor',
}

CONFIG_FILES = {
    'package.json', 'requirements.txt', 'Pipfile', 'composer.json',
    'Gemfile', 'Cargo.toml', 'go.mod', 'pom.xml', 'build.gradle',
    'docker-compose.yml', 'Dockerfile', '.env.example', '.env.sample',
}

def is_scannable(filepath):
    """Determine if a file should be scanned."""
    path = Path(filepath)
    if any(d in path.parts for d in IGNORE_DIRS):
        return False
    if path.name.endswith('.min.js') or path.name.endswith('.min.css'):
        return False
    if path.suffix in CODE_EXTENSIONS or path.name in CONFIG_FILES:
        return True
    return False

# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------

def scan_file(filepath, patterns_dict):
    """Scan a single file against a dictionary of pattern groups."""
    results = defaultdict(list)
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception:
        return results

    for group_name, pattern_list in patterns_dict.items():
        for regex, description in pattern_list:
            for match in re.finditer(regex, content, re.IGNORECASE | re.DOTALL):
                start = max(0, match.start() - 80)
                end = min(len(content), match.end() + 80)
                context = content[start:end].replace('\n', ' ').strip()
                value = match.group(1) if match.lastindex and match.lastindex >= 1 else match.group(0)
                line_num = content.count('\n', 0, match.start()) + 1
                results[group_name].append({
                    "file": str(filepath),
                    "line": line_num,
                    "match": value.strip()[:200],
                    "description": description,
                    "context": context[:300],
                })
    return results

def detect_tech_stack(repo_path):
    """Detect the backend technology stack of the repository."""
    stack = {"backend": [], "integrations": []}
    repo = Path(repo_path)

    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for f in files:
            if f == "package.json":
                try:
                    pkg = json.loads((Path(root) / f).read_text(errors='ignore'))
                    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                    if "next" in deps:
                        stack["backend"].append("Next.js API Routes")
                    if "nuxt" in deps:
                        stack["backend"].append("Nuxt Server")
                    if "express" in deps:
                        stack["backend"].append("Express.js")
                    if "facebook-nodejs-business-sdk" in deps:
                        stack["integrations"].append("Meta Business SDK (Node.js)")
                except Exception:
                    pass
            elif f == "requirements.txt" or f == "Pipfile":
                try:
                    content = (Path(root) / f).read_text(errors='ignore')
                    if "django" in content.lower():
                        stack["backend"].append("Django")
                    if "flask" in content.lower():
                        stack["backend"].append("Flask")
                    if "fastapi" in content.lower():
                        stack["backend"].append("FastAPI")
                    if "facebook-business" in content.lower():
                        stack["integrations"].append("Meta Business SDK (Python)")
                except Exception:
                    pass
            elif f == "composer.json":
                try:
                    pkg = json.loads((Path(root) / f).read_text(errors='ignore'))
                    deps = pkg.get("require", {})
                    if "laravel/framework" in deps:
                        stack["backend"].append("Laravel")
                    if "facebook/php-business-sdk" in deps:
                        stack["integrations"].append("Meta Business SDK (PHP)")
                except Exception:
                    pass

    # Deduplicate
    for key in stack:
        stack[key] = list(dict.fromkeys(stack[key]))
    return stack

def audit_repo(repo_path):
    """Run the full CAPI audit on a repository."""
    repo_path = Path(repo_path)

    # Detect tech stack
    tech_stack = detect_tech_stack(repo_path)

    # Scan all files
    capi_findings = defaultdict(list)
    hashing_findings = []
    security_findings = []
    cookie_findings = []
    scanned_files = 0
    file_list = []

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for fname in files:
            filepath = Path(root) / fname
            if is_scannable(str(filepath)):
                scanned_files += 1
                rel_path = str(filepath.relative_to(repo_path))
                file_list.append(rel_path)

                # CAPI patterns
                for group, matches in scan_file(filepath, CAPI_PATTERNS).items():
                    for m in matches:
                        m["file"] = rel_path
                    capi_findings[group].extend(matches)

                # Hashing
                for regex, desc in HASHING_PATTERNS:
                    try:
                        content = filepath.read_text(errors='ignore')
                    except Exception:
                        continue
                    for match in re.finditer(regex, content, re.IGNORECASE):
                        line_num = content.count('\n', 0, match.start()) + 1
                        hashing_findings.append({
                            "file": rel_path, "line": line_num,
                            "match": match.group(0)[:100], "description": desc,
                        })

                # Security
                for regex, desc in SECURITY_PATTERNS:
                    try:
                        content = filepath.read_text(errors='ignore')
                    except Exception:
                        continue
                    for match in re.finditer(regex, content):
                        line_num = content.count('\n', 0, match.start()) + 1
                        security_findings.append({
                            "file": rel_path, "line": line_num,
                            "match": "[REDACTED]", "description": desc,
                        })

                # Cookie handling
                for regex, desc in COOKIE_PATTERNS:
                    try:
                        content = filepath.read_text(errors='ignore')
                    except Exception:
                        continue
                    for match in re.finditer(regex, content, re.IGNORECASE):
                        line_num = content.count('\n', 0, match.start()) + 1
                        cookie_findings.append({
                            "file": rel_path, "line": line_num,
                            "match": match.group(0)[:100], "description": desc,
                        })

    # -----------------------------------------------------------------------
    # Derive Summary
    # -----------------------------------------------------------------------

    has_capi = bool(capi_findings.get("endpoint") or capi_findings.get("sdk_python") or
                    capi_findings.get("sdk_node") or capi_findings.get("sdk_php") or
                    capi_findings.get("sdk_ruby") or capi_findings.get("sdk_classes"))

    capi_status = "Implemented" if has_capi else "Not Found"

    # Deduplication
    has_server_dedup = bool(capi_findings.get("dedup_server"))
    dedup_status = "Configured (Server-side event_id found)" if has_server_dedup else "Not Configured"

    # CAPI user data coverage
    user_data_fields = list({m["description"] for m in capi_findings.get("payload_user_data", [])})

    # CAPI required fields
    capi_required_fields = list({m["description"] for m in capi_findings.get("payload_required", [])})

    # CAPI SDK method
    capi_method = "None"
    if capi_findings.get("sdk_python"):
        capi_method = "Meta Business SDK (Python)"
    elif capi_findings.get("sdk_node"):
        capi_method = "Meta Business SDK (Node.js)"
    elif capi_findings.get("sdk_php"):
        capi_method = "Meta Business SDK (PHP)"
    elif capi_findings.get("sdk_ruby"):
        capi_method = "Meta Business SDK (Ruby)"
    elif capi_findings.get("endpoint"):
        capi_method = "Direct HTTP API"

    # Cookie handling
    has_cookie_handling = bool(cookie_findings)

    summary = {
        "scanned_files": scanned_files,
        "tech_stack": tech_stack,
        "capi_status": capi_status,
        "capi_method": capi_method,
        "capi_required_fields": capi_required_fields,
        "capi_user_data_fields": user_data_fields,
        "deduplication_status": dedup_status,
        "has_hashing": bool(hashing_findings),
        "has_cookie_handling": has_cookie_handling,
        "has_hardcoded_token": bool(security_findings),
        "findings": {
            "capi": dict(capi_findings),
            "hashing": hashing_findings,
            "security": security_findings,
            "cookies": cookie_findings,
        },
    }
    return summary

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit a repository for Meta CAPI implementation.")
    parser.add_argument("repo_path", help="Path to the cloned repository directory")
    parser.add_argument("--output", "-o", default="capi_audit_results.json", help="Output JSON file path")
    args = parser.parse_args()

    print(f"Scanning repository at {args.repo_path} for CAPI patterns...")
    results = audit_repo(args.repo_path)

    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nScan complete. Scanned {results['scanned_files']} files.")
    print(f"Backend Tech Stack: {results['tech_stack']['backend']}")
    print(f"CAPI Status: {results['capi_status']}")
    print(f"CAPI Method: {results['capi_method']}")
    print(f"Deduplication: {results['deduplication_status']}")
    print(f"Hashing Found: {results['has_hashing']}")
    print(f"Cookie Handling: {results['has_cookie_handling']}")
    print(f"Hardcoded Token: {results['has_hardcoded_token']}")
    print(f"\nResults saved to {args.output}")
