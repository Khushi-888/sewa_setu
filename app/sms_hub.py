# -*- coding: utf-8 -*-
"""
Central SMS hub for PurvSMS simulation.
Provides thread-safe storage for dispatched OTPs and SMS notifications,
shared between the Flask portal, MCP tools, and the FastAPI API gateway.
"""

import time
from typing import List, Dict, Any

SMS_STORE: List[Dict[str, Any]] = []


def record_sms(mobile: str, text: str) -> Dict[str, Any]:
    """Record an outgoing SMS message."""
    now = time.time()
    msg = {
        "id": len(SMS_STORE) + 1,
        "to": (mobile or "").strip(),
        "text": (text or "").strip(),
        "sent_at": now,
        "delivery_at": now + 1.0,
        "delivered": True
    }
    SMS_STORE.append(msg)
    return msg


def get_messages(to_filter: str = "") -> List[Dict[str, Any]]:
    """Retrieve messages, optionally filtered by recipient mobile."""
    now = time.time()
    out = []
    clean_filter = (to_filter or "").strip()
    for m in SMS_STORE:
        if clean_filter and m["to"] != clean_filter:
            continue
        is_deliv = now >= m["delivery_at"]
        out.append({
            "id": m["id"],
            "to": m["to"],
            "text": m["text"] if is_deliv else None,
            "delivered": is_deliv,
            "sent_at": m["sent_at"],
            "delivery_at": m["delivery_at"]
        })
    return out
