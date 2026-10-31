# -*- coding: utf-8 -*-
"""Unit and integration tests for Block Officer MCP Server."""

import os
import sys
import asyncio
import json

APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app"))
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for d in (ROOT_DIR, APP_DIR):
    if d not in sys.path:
        sys.path.insert(0, d)

os.environ["DB_HOST"] = os.environ.get("DB_HOST", "localhost")
os.environ["SMS_GATEWAY_URL"] = os.environ.get("SMS_GATEWAY_URL", "http://localhost:8025")

from mcp_servers.officer_mcp import officer_server
from mcp_servers.citizen_mcp import citizen_server
import app as portal


async def test_officer_workload_summary():
    res = await officer_server.call_tool("get_officer_workload_summary", {"block": "Sonari"})
    assert not res.is_error
    data = res.content[0].text
    assert "pending_applications" in data
    assert "Sonari" in data


async def test_list_pending_queue():
    res = await officer_server.call_tool("list_pending_queue", {"block": "Sonari", "sort_by_sla": True, "limit": 5})
    assert not res.is_error
    data = res.content[0].text
    assert "applications" in data
    assert "total_pending" in data


async def test_officer_decision_lifecycle():
    # Submit an application via citizen MCP first
    sub_res = await citizen_server.call_tool("submit_pension_application", {
        "applicant_name": "Officer Test Pensioner",
        "dob": "12/12/1952",
        "gender": "Male",
        "marital_status": "Married",
        "village": "Lakhipur",
        "block": "Sonari",
        "bank_account": "987654321098",
        "ifsc": "SBIN0003077",
        "mobile": "9123456780"
    })
    assert not sub_res.is_error

    # Officer retrieves dossier
    dos_res = await officer_server.call_tool("get_application_dossier", {"application_id_or_no": "Officer Test Pensioner"})
    assert not dos_res.is_error
    assert "Officer Test Pensioner" in dos_res.content[0].text

    # Officer attempts decision with empty note (must fail)
    fail_res = await officer_server.call_tool("decide_application", {
        "application_id_or_no": "Officer Test Pensioner",
        "decision": "APPROVED",
        "note": ""
    })
    assert "required" in fail_res.content[0].text.lower() or "error" in fail_res.content[0].text.lower()

    # Officer makes reasoned approval
    note_text = "Verified age proof and residential credentials at block headquarters."
    appr_res = await officer_server.call_tool("decide_application", {
        "application_id_or_no": "Officer Test Pensioner",
        "decision": "APPROVED",
        "note": note_text,
        "officer_username": "aruna.bdo"
    })
    assert not appr_res.is_error
    assert "APPROVED" in appr_res.content[0].text

    # Review audit trail
    aud_res = await officer_server.call_tool("review_audit_trail", {"application_id_or_no": "Officer Test Pensioner"})
    assert not aud_res.is_error
    assert "aruna.bdo" in aud_res.content[0].text


if __name__ == "__main__":
    asyncio.run(test_officer_workload_summary())
    asyncio.run(test_list_pending_queue())
    asyncio.run(test_officer_decision_lifecycle())
    print("All Officer MCP tests passed successfully!")
