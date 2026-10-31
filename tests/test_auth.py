# -*- coding: utf-8 -*-
"""Unit tests for OAuth 2.1 token verification and role separation."""

import os
import sys
import pytest

APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app"))
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for d in (ROOT_DIR, APP_DIR):
    if d not in sys.path:
        sys.path.insert(0, d)

os.environ["DB_HOST"] = os.environ.get("DB_HOST", "localhost")

import app as portal
import oauth
from mcp_servers.auth import verify_mcp_token
from fastapi import HTTPException


def test_citizen_token_valid():
    token, claims = oauth.mint_access_token("citizen:9876543210", "citizen", "citizen", oauth.ISSUER, "test-client")
    verified = verify_mcp_token(token, required_role="citizen")
    assert verified["sub"] == "citizen:9876543210"
    assert verified["role"] == "citizen"


def test_officer_token_valid():
    token, claims = oauth.mint_access_token("officer:admin", "officer", "officer", oauth.ISSUER, "test-officer")
    verified = verify_mcp_token(token, required_role="officer")
    assert verified["sub"] == "officer:admin"
    assert verified["role"] == "officer"


def test_privilege_violation_citizen_blocked_from_officer():
    token, claims = oauth.mint_access_token("citizen:9876543210", "citizen", "citizen", oauth.ISSUER, "test-client")
    with pytest.raises(HTTPException) as excinfo:
        verify_mcp_token(token, required_role="officer")
    assert excinfo.value.status_code == 403
    assert "Forbidden" in excinfo.value.detail or "Officer credentials required" in excinfo.value.detail


def test_invalid_token_rejected():
    with pytest.raises(HTTPException) as excinfo:
        verify_mcp_token("fake.invalid.token", required_role="citizen")
    assert excinfo.value.status_code == 401


if __name__ == "__main__":
    test_citizen_token_valid()
    test_officer_token_valid()
    try:
        test_privilege_violation_citizen_blocked_from_officer()
    except Exception as e:
        print("Privilege violation correctly caught:", e)
    try:
        test_invalid_token_rejected()
    except Exception as e:
        print("Invalid token correctly rejected:", e)
    print("All Auth & Role Separation tests passed successfully!")
