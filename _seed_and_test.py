"""Seed test data and call the investigation endpoint."""
import httpx
import hashlib
import json
import sys
import time

BASE = "http://localhost:8001"
DASHBOARD_CREDS = ("admin", "changeme")

# ---- 1. Check health ----
r = httpx.get(f"{BASE}/health")
print(f"Health: {r.status_code} {r.json()['status']}")

# ---- 2. Register a branch (returns API key) ----
r = httpx.post(
    f"{BASE}/v1/branches/register",
    json={
        "id": "branch-001",
        "name": "First National Downtown",
        "bank_name": "First National Bank",
        "city": "Austin",
        "state": "TX",
    },
)
print(f"Register branch: {r.status_code}")
if r.status_code == 201:
    api_key = r.json()["api_key"]
    print(f"API key obtained: {api_key[:20]}...")
elif r.status_code == 409:
    print("Branch already exists, rotating key...")
    r = httpx.post(f"{BASE}/v1/branches/rotate-key", params={"branch_id": "branch-001"})
    api_key = r.json()["api_key"]
    print(f"API key obtained: {api_key[:20]}...")
else:
    print(f"  Response: {r.text}")
    sys.exit(1)

# ---- 3. Submit a suspicious check fingerprint ----
fingerprint = hashlib.sha256(b"suspicious-check-12345").hexdigest()
headers = {"X-API-Key": api_key}

r = httpx.post(
    f"{BASE}/v1/checks/fingerprint",
    json={
        "fingerprint": fingerprint,
        "features": {
            "edge_density": 0.92,
            "texture_variance": 0.15,
        },
        "branch_id": "branch-001",
        "suspect_identifier": hashlib.sha256(b"john-doe-suspect").hexdigest(),
    },
    headers=headers,
)
print(f"Submit check: {r.status_code}")
if r.status_code != 200:
    print(f"  Response: {r.text}")
    sys.exit(1)

check_resp = r.json()
print(f"  Fraud score: {check_resp['fraud_score']}, Is fraud: {check_resp['is_fraud']}")

# ---- 5. Get the check ID (we need it for investigate) ----
# The fingerprint endpoint doesn't return check_id directly, so query by fingerprint
r = httpx.get(
    f"{BASE}/v1/checks/fingerprint/{fingerprint}",
    headers=headers,
)
print(f"Get fingerprint history: {r.status_code}")

# We need to get check_id from the detail endpoint or use a different approach
# Let's flag the check first by finding the check ID
# The check ID should be 1 since this is a fresh DB
check_id = 1

# ---- 6. Flag the check (bank manager workflow) ----
r = httpx.post(
    f"{BASE}/v1/checks/{check_id}/flag",
    json={
        "severity": "high",
        "notes": "Customer presented check with visible alterations - ink color mismatch, possible amount modification",
        "flagged_by": "manager_smith",
    },
    headers=headers,  # Use X-API-Key header (accepted by get_dashboard_auth)
)
print(f"Flag check: {r.status_code}")
if r.status_code == 200:
    print(f"  Alert ID: {r.json()['alert_id']}")

# ---- 7. Call the investigation endpoint ----
print("\n=== RUNNING AI INVESTIGATION ===")
print("(This calls Claude 3 times - forensic analyst, risk scorer, report generator)")
print("Waiting for pipeline to complete...\n")

r = httpx.post(
    f"{BASE}/v1/checks/{check_id}/investigate",
    headers=headers,  # Use X-API-Key header (accepted by get_dashboard_auth)
    timeout=120.0,  # 2 min timeout - 3 LLM calls can take a while
)

print(f"Investigation: {r.status_code}")
if r.status_code == 200:
    result = r.json()
    print(f"\n{'='*60}")
    print("FORENSIC TIMELINE (first 500 chars):")
    print(f"{'='*60}")
    print(result["forensic_timeline"][:500])
    print(f"\n{'='*60}")
    print("RISK ASSESSMENT (first 500 chars):")
    print(f"{'='*60}")
    print(result["risk_assessment"][:500])
    print(f"\n{'='*60}")
    print("SAR REPORT (first 500 chars):")
    print(f"{'='*60}")
    print(result["sar_report"][:500])
    print(f"\n{'='*60}")
    print("SUCCESS - All 3 pipeline stages produced output")
    print(f"Generated at: {result['generated_at']}")
else:
    print(f"FAILED: {r.text[:500]}")

