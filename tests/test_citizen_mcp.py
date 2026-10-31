# -*- coding: utf-8 -*-
"""Unit and integration tests for Citizen MCP Server."""

import os
import sys
import asyncio
import pytest

APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app"))
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for d in (ROOT_DIR, APP_DIR):
    if d not in sys.path:
        sys.path.insert(0, d)

os.environ["DB_HOST"] = os.environ.get("DB_HOST", "localhost")

from mcp_servers.citizen_mcp import citizen_server


@pytest.mark.asyncio
async def test_get_scheme_guidelines():
    res = await citizen_server.call_tool("get_scheme_guidelines", {"block": "Sonari"})
    assert not res.is_error
    data = res.content[0].text
    assert "₹250 per month" in data
    assert "Sonari" in data


@pytest.mark.asyncio
async def test_check_eligibility_valid():
    res = await citizen_server.call_tool("check_eligibility", {"dob": "15/08/1955", "block": "Sonari"})
    assert not res.is_error
    data = res.content[0].text
    assert "true" in data.lower() or "eligible" in data.lower()


@pytest.mark.asyncio
async def test_check_eligibility_underage():
    res = await citizen_server.call_tool("check_eligibility", {"dob": "15/08/1975", "block": "Sonari"})
    assert not res.is_error
    data = res.content[0].text
    assert "false" in data.lower()
    assert "minimum age" in data.lower()


@pytest.mark.asyncio
async def test_otp_and_submission_lifecycle():
    mobile = "9988776655"
    # Clean any prior application for test mobile
    import app as portal
    conn = portal.get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM applications WHERE mobile = %s", (mobile,))
    cur.execute("DELETE FROM portal_users WHERE mobile = %s", (mobile,))
    conn.commit()
    cur.close()
    conn.close()

    # Request OTP
    otp_res = await citizen_server.call_tool("request_otp", {"mobile": mobile})
    assert not otp_res.is_error

    # Submit application
    sub_res = await citizen_server.call_tool("submit_pension_application", {
        "applicant_name": "Test Citizen",
        "dob": "10/05/1950",
        "gender": "Female",
        "marital_status": "Widowed",
        "village": "Lakhipur",
        "block": "Sonari",
        "bank_account": "123456789012",
        "ifsc": "SBIN0003077",
        "mobile": mobile
    })
    assert not sub_res.is_error
    assert "PENDING" in sub_res.content[0].text

    # Check status
    st_res = await citizen_server.call_tool("check_application_status", {"mobile": mobile})
    assert not st_res.is_error
    assert "Test Citizen" in st_res.content[0].text


if __name__ == "__main__":
    asyncio.run(test_get_scheme_guidelines())
    asyncio.run(test_check_eligibility_valid())
    asyncio.run(test_check_eligibility_underage())
    asyncio.run(test_otp_and_submission_lifecycle())
    print("All Citizen MCP tests passed successfully!")
