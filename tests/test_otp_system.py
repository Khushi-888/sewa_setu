# -*- coding: utf-8 -*-
"""
Verification script for Sewa Setu OTP system:
Tests web portal flow, simulated telecom carrier, citizen MCP tools, and security validation.
"""

import re
import json
import time
import requests
import psycopg2

BASE = "http://127.0.0.1:8000"
DB_URL = "postgresql://postgres:postgres@localhost:5432/sewasetu"


def test_web_portal_otp():
    print("\n--- 1. Testing Web Portal OTP Flow ---")
    s = requests.Session()
    
    # Step 1: Request apply page
    r_apply = s.get(f"{BASE}/apply")
    assert r_apply.status_code == 200
    
    # Solve math captcha
    match = re.search(r"(\d+)\s*\+\s*(\d+)", r_apply.text)
    assert match, "Captcha not found"
    captcha_val = int(match.group(1)) + int(match.group(2))
    test_mobile = "9876543210"
    
    # Step 2: Post mobile and captcha
    r_sub = s.post(f"{BASE}/apply", data={"mobile": test_mobile, "captcha": str(captcha_val)}, allow_redirects=True)
    assert r_sub.status_code == 200
    assert "/verify" in r_sub.url, f"Expected /verify, got {r_sub.url}"
    print("  [OK] Successfully requested OTP for mobile", test_mobile)

    # Step 3: Check OTP banner on page or database
    banner_match = re.search(r'id=["\']banner-otp["\']>(\d{6})<', r_sub.text)
    if banner_match:
        otp_code = banner_match.group(1)
        print(f"  [OK] Banner displayed live carrier OTP: {otp_code}")
    else:
        # Check DB
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("SELECT code FROM otps WHERE mobile = %s ORDER BY id DESC LIMIT 1", (test_mobile,))
        otp_code = cur.fetchone()[0]
        cur.close()
        conn.close()
        print(f"  [OK] Retrieved generated OTP from PostgreSQL: {otp_code}")

    # Step 4: Verify OTP submission
    r_ver = s.post(f"{BASE}/verify", data={"otp": otp_code}, allow_redirects=True)
    assert r_ver.status_code == 200
    assert "/form/1" in r_ver.url, f"Expected redirect to /form/1, got {r_ver.url}"
    print("  [OK] Successfully authenticated citizen and redirected to Step 1 of form!")


def test_mcp_otp_tools():
    print("\n--- 2. Testing Citizen MCP Tool (request_otp & verify_otp) ---")
    test_mobile = "9876500055"
    
    # Step 1: Invoke request_otp tool
    req_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "request_otp",
            "arguments": {"mobile": test_mobile}
        }
    }
    r1 = requests.post(f"{BASE}/mcp/citizen", json=req_payload)
    assert r1.status_code == 200
    res1 = json.loads(r1.json()["result"]["content"][0]["text"])
    assert res1["success"] is True
    print(f"  [OK] MCP request_otp successful: {res1['message']}")

    # Step 2: Fetch dispatched OTP from DB
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT code FROM otps WHERE mobile = %s ORDER BY id DESC LIMIT 1", (test_mobile,))
    dispatched_code = cur.fetchone()[0]
    cur.close()
    conn.close()
    print(f"  [OK] Database confirmed OTP row: {dispatched_code}")

    # Step 3: Invoke verify_otp tool with correct code
    ver_payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "verify_otp",
            "arguments": {"mobile": test_mobile, "otp": dispatched_code}
        }
    }
    r2 = requests.post(f"{BASE}/mcp/citizen", json=ver_payload)
    assert r2.status_code == 200
    res2 = json.loads(r2.json()["result"]["content"][0]["text"])
    assert res2["verified"] is True
    print(f"  [OK] MCP verify_otp successfully verified code: {res2['message']}")

    # Step 4: Invoke verify_otp tool with wrong code
    wrong_payload = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "verify_otp",
            "arguments": {"mobile": test_mobile, "otp": "000000"}
        }
    }
    r3 = requests.post(f"{BASE}/mcp/citizen", json=wrong_payload)
    assert r3.status_code == 200
    res3 = json.loads(r3.json()["result"]["content"][0]["text"])
    assert res3["verified"] is False
    print(f"  [OK] MCP verify_otp rejected incorrect code: {res3['error']}")


def test_carrier_sms_console():
    print("\n--- 3. Testing Telecom Carrier Console (/sms-console & /api/messages) ---")
    r = requests.get(f"{BASE}/api/messages")
    assert r.status_code == 200
    messages = r.json().get("messages", [])
    print(f"  [OK] Dispatched messages recorded in carrier hub: {len(messages)}")
    if messages:
        print(f"  [OK] Latest carrier message: To: {messages[-1]['to']} | Body: {messages[-1]['text']}")


if __name__ == "__main__":
    test_web_portal_otp()
    test_mcp_otp_tools()
    test_carrier_sms_console()
    print("\n[ALL OTP SYSTEMS FULLY OPERATIONAL AND VERIFIED!]")
