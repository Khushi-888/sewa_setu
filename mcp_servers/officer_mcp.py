# -*- coding: utf-8 -*-
"""
Block Officer MCP Server for Sewa Setu Old Age Pension Scheme.
Endpoint: /mcp/officer
Scope: officer

Enables Block Development Officers (BDOs) and welfare case workers to:
  - View overall queue workload, SLA risk metrics, and block distributions
  - Inspect pending applications sorted by statutory 15-day SLA urgency
  - Access comprehensive case dossiers (identity, bank details, age proof, audit trail)
  - Record official approve / reject decisions with mandatory recorded rationale
  - Maintain complete administrative accountability under the RTPS Act
"""

import os
import sys
import re
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

# Add app path for canonical portal logic
APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app"))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

import app as portal
from mcp.server.mcpserver import MCPServer

logger = logging.getLogger("sewasetu.mcp.officer")

officer_server = MCPServer(
    name="sewasetu-officer-assistant",
    version="1.0.0",
    description="Official Block Officer Assistant for Sewa Setu (Department of Social Welfare, Purvanchal).",
    instructions="You are the official Sewa Setu Block Officer Executive Assistant. Assist block development officers in managing the pension review queue, prioritizing cases approaching statutory 15-day RTPS deadlines, inspecting applicant dossiers, and recording reasoned decisions with full administrative integrity."
)


# ---------------------------------------------------------------------------
# MCP Resources
# ---------------------------------------------------------------------------

@officer_server.resource("sewasetu://officer/sla-standards")
def officer_sla_resource() -> str:
    """Statutory guidelines and review procedures for Block Development Officers."""
    return f"""
GOVERNMENT OF PURVANCHAL - STATUTORY OFFICER DIRECTIVES
UNDER THE PURVANCHAL RIGHT TO PUBLIC SERVICES ACT (RTPS)

1. STATUTORY SLA: Applications MUST be reviewed and decided within {portal.SLA_DAYS} calendar days of submission.
2. AUTOMATIC DEEMED APPROVAL: Any pending application exceeding {portal.SLA_DAYS} days will automatically stand approved by the system ('DEEMED_APPROVED').
3. MANDATORY RATIONALE: Every manual decision (APPROVED or REJECTED) requires an official recorded reason saved permanently against the officer's name in the audit trail.
4. VERIFICATION CRITERIA:
   - Age verification: Document must corroborate age >= {portal.MIN_AGE}.
   - Bank verification: Valid IFSC format and active savings account.
   - Jurisdiction check: Village must belong to the officer's administrative block.
"""


# ---------------------------------------------------------------------------
# Officer Tools
# ---------------------------------------------------------------------------

@officer_server.tool()
def get_officer_workload_summary(block: Optional[str] = None) -> Dict[str, Any]:
    """
    Get a high-level workload overview: total pending applications, cases at risk of SLA breach (>10 days),
    and block-by-block distribution.

    Args:
        block: Optional filter for a specific block (e.g. 'Sonari').
    """
    try:
        conn = portal.get_db()
        cur = conn.cursor()

        # Overall status counts
        cur.execute("SELECT status, count(*) FROM applications GROUP BY status")
        status_counts = dict(cur.fetchall())

        # SLA threshold calculation
        sla_cutoff = datetime.now() - timedelta(days=portal.SLA_DAYS)
        urgent_cutoff = datetime.now() - timedelta(days=10)

        # Overdue / approaching SLA
        if block:
            cur.execute("SELECT count(*) FROM applications WHERE status = 'PENDING' AND block = %s", (block,))
            pending_count = cur.fetchone()[0]

            cur.execute("SELECT count(*) FROM applications WHERE status = 'PENDING' AND block = %s AND submitted_at < %s",
                        (block, urgent_cutoff))
            urgent_count = cur.fetchone()[0]

            cur.execute("SELECT count(*) FROM applications WHERE status = 'PENDING' AND block = %s AND submitted_at < %s",
                        (block, sla_cutoff))
            overdue_count = cur.fetchone()[0]
        else:
            pending_count = status_counts.get("PENDING", 0)
            
            cur.execute("SELECT count(*) FROM applications WHERE status = 'PENDING' AND submitted_at < %s",
                        (urgent_cutoff,))
            urgent_count = cur.fetchone()[0]

            cur.execute("SELECT count(*) FROM applications WHERE status = 'PENDING' AND submitted_at < %s",
                        (sla_cutoff,))
            overdue_count = cur.fetchone()[0]

        # Block-wise breakdown of pending applications
        cur.execute("SELECT block, count(*) FROM applications WHERE status = 'PENDING' GROUP BY block ORDER BY count(*) DESC")
        pending_by_block = dict(cur.fetchall())

        cur.close()
        conn.close()

        return {
            "queried_block": block or "All Blocks",
            "pending_applications": pending_count,
            "urgent_sla_risk_applications": urgent_count,
            "overdue_applications": overdue_count,
            "statutory_sla_days": portal.SLA_DAYS,
            "system_totals": status_counts,
            "pending_by_block": pending_by_block,
            "advisory": f"{urgent_count} cases have been pending for >10 days and require immediate review before RTPS statutory deemed approval triggers." if urgent_count > 0 else "All queues within safe SLA limits."
        }
    except Exception as e:
        logger.error("Error retrieving workload summary: %s", e)
        return {"error": f"Failed to retrieve workload summary: {str(e)}"}


@officer_server.tool()
def list_pending_queue(
    block: Optional[str] = None,
    sort_by_sla: bool = True,
    limit: int = 20,
    page: int = 1
) -> Dict[str, Any]:
    """
    List pending applications for review. By default, applications are sorted by oldest submission first
    so the cases closest to statutory 15-day deemed approval are reviewed with highest priority.

    Args:
        block: Optional administrative block filter (e.g. 'Sonari').
        sort_by_sla: If True, sorts by oldest submitted first (highest SLA urgency).
        limit: Number of applications to return per page (max 50).
        page: Page number for pagination (starts at 1).
    """
    clean_limit = max(1, min(limit, 50))
    clean_offset = (max(1, page) - 1) * clean_limit

    try:
        conn = portal.get_db()
        cur = conn.cursor()

        order_clause = "ORDER BY submitted_at ASC" if sort_by_sla else "ORDER BY submitted_at DESC"
        
        if block:
            cur.execute(
                f"""SELECT id, application_no, applicant_name, mobile, village, block, submitted_at
                    FROM applications WHERE status = 'PENDING' AND block = %s
                    {order_clause} LIMIT %s OFFSET %s""",
                (block.strip(), clean_limit, clean_offset)
            )
            cur.execute("SELECT count(*) FROM applications WHERE status = 'PENDING' AND block = %s", (block.strip(),))
            total_matching = cur.fetchone()[0]
        else:
            cur.execute(
                f"""SELECT id, application_no, applicant_name, mobile, village, block, submitted_at
                    FROM applications WHERE status = 'PENDING'
                    {order_clause} LIMIT %s OFFSET %s""",
                (clean_limit, clean_offset)
            )
            cur.execute("SELECT count(*) FROM applications WHERE status = 'PENDING'")
            total_matching = cur.fetchone()[0]

        rows = cur.fetchall()
        cur.close()
        conn.close()

        now = datetime.now()
        results = []
        for r in rows:
            app_id, app_no, name, mob, village, b_block, sub_at = r
            days_pending = (now - sub_at).days if sub_at else 0
            sla_left = max(0, portal.SLA_DAYS - days_pending)
            
            sla_status = "NORMAL"
            if days_pending >= portal.SLA_DAYS:
                sla_status = "OVERDUE (Will be Deemed Approved)"
            elif days_pending >= 10:
                sla_status = "CRITICAL (<= 5 days left)"

            results.append({
                "id": app_id,
                "application_no": app_no,
                "applicant_name": name,
                "mobile": f"XXXXXX{mob[-4:]}",
                "village": village,
                "block": b_block,
                "submitted_at": sub_at.strftime("%Y-%m-%d %H:%M") if sub_at else "",
                "days_pending": days_pending,
                "sla_days_remaining": sla_left,
                "sla_urgency": sla_status
            })

        return {
            "total_pending": total_matching,
            "page": page,
            "limit": clean_limit,
            "block_filter": block or "All",
            "sorted_by_sla": sort_by_sla,
            "applications": results
        }
    except Exception as e:
        logger.error("Error listing pending queue: %s", e)
        return {"error": f"Failed to list pending queue: {str(e)}"}


@officer_server.tool()
def get_application_dossier(application_id_or_no: str) -> Dict[str, Any]:
    """
    Retrieve full applicant dossier for case review: identity, age, address, bank details,
    uploaded document status, and complete chronological audit log.

    Args:
        application_id_or_no: Either numeric ID (e.g. '100001') or application number (e.g. 'SSP26123456').
    """
    query_str = str(application_id_or_no).strip()
    try:
        conn = portal.get_db()
        cur = conn.cursor()

        if query_str.isdigit():
            cur.execute(
                """SELECT id, application_no, applicant_name, mobile, dob, gender, marital_status,
                          husband_name, village, block, bank_account, ifsc, doc_path, status,
                          submitted_at, decided_at, decided_by
                   FROM applications WHERE id = %s""", (int(query_str),)
            )
        elif query_str.upper().startswith("SSP"):
            cur.execute(
                """SELECT id, application_no, applicant_name, mobile, dob, gender, marital_status,
                          husband_name, village, block, bank_account, ifsc, doc_path, status,
                          submitted_at, decided_at, decided_by
                   FROM applications WHERE application_no = %s""", (query_str,)
            )
        else:
            cur.execute(
                """SELECT id, application_no, applicant_name, mobile, dob, gender, marital_status,
                          husband_name, village, block, bank_account, ifsc, doc_path, status,
                          submitted_at, decided_at, decided_by
                   FROM applications WHERE application_no = %s OR applicant_name ILIKE %s
                   ORDER BY id DESC LIMIT 1""", (query_str, f"%{query_str}%")
            )

        row = cur.fetchone()
        if not row:
            cur.close()
            conn.close()
            return {"error": f"Application '{query_str}' not found in portal database."}

        (app_id, app_no, name, mob, dob, gender, marital, husband, village, block,
         bank_acct, ifsc, doc_path, status, sub_at, dec_at, dec_by) = row

        # Fetch audit history
        cur.execute("SELECT at, action, actor, note FROM audit_log WHERE application_id = %s ORDER BY at ASC",
                    (app_id,))
        audit_records = cur.fetchall()
        cur.close()
        conn.close()

        # Compute age & SLA
        current_age = portal.age_on(dob, portal.now_ist().date()) if dob else None
        now = datetime.now()
        days_pending = (now - sub_at).days if sub_at else 0
        sla_days_left = max(0, portal.SLA_DAYS - days_pending) if status == "PENDING" else 0

        # Check document presence
        doc_exists = os.path.exists(doc_path) if doc_path else False

        return {
            "id": app_id,
            "application_no": app_no,
            "personal_details": {
                "applicant_name": name,
                "dob": dob.strftime("%d/%m/%Y") if dob else "",
                "calculated_age": current_age,
                "age_eligible": current_age >= portal.MIN_AGE if current_age else False,
                "gender": gender,
                "marital_status": marital,
                "husband_name": husband or "N/A"
            },
            "contact_and_residence": {
                "mobile": mob,
                "village": village,
                "block": block,
                "block_valid": block in portal.BLOCKS
            },
            "banking_details": {
                "bank_account": bank_acct,
                "ifsc": ifsc,
                "account_valid": bool(re.fullmatch(r"\d{9,18}", bank_acct or "")),
                "ifsc_valid": bool(re.fullmatch(r"[A-Z]{4}0[A-Z0-9]{6}", ifsc or ""))
            },
            "document_verification": {
                "document_path": doc_path,
                "file_exists_on_server": doc_exists,
                "document_name": os.path.basename(doc_path or "")
            },
            "status_and_sla": {
                "status": status,
                "submitted_at": sub_at.strftime("%Y-%m-%d %H:%M:%S") if sub_at else "",
                "decided_at": dec_at.strftime("%Y-%m-%d %H:%M:%S") if dec_at else None,
                "decided_by": dec_by,
                "days_pending": days_pending,
                "sla_days_remaining": sla_days_left,
                "statutory_sla_breached": days_pending >= portal.SLA_DAYS if status == "PENDING" else False
            },
            "audit_trail": [
                {
                    "timestamp": a[0].strftime("%Y-%m-%d %H:%M:%S") if a[0] else "",
                    "action": a[1],
                    "actor": a[2],
                    "note": a[3] or ""
                }
                for a in audit_records
            ]
        }
    except Exception as e:
        logger.error("Error retrieving dossier: %s", e)
        return {"error": f"Failed to retrieve dossier: {str(e)}"}


@officer_server.tool()
def review_audit_trail(application_id_or_no: str) -> Dict[str, Any]:
    """
    Get the chronological audit log for an application: who took what action, when, and with what note.

    Args:
        application_id_or_no: Numeric application ID or application number (e.g. 'SSP26123456').
    """
    query_str = str(application_id_or_no).strip()
    try:
        conn = portal.get_db()
        cur = conn.cursor()

        if query_str.isdigit():
            cur.execute("SELECT id, application_no FROM applications WHERE id = %s", (int(query_str),))
        elif query_str.upper().startswith("SSP"):
            cur.execute("SELECT id, application_no FROM applications WHERE application_no = %s", (query_str,))
        else:
            cur.execute("SELECT id, application_no FROM applications WHERE application_no = %s OR applicant_name ILIKE %s ORDER BY id DESC LIMIT 1",
                        (query_str, f"%{query_str}%"))
        
        row = cur.fetchone()
        if not row:
            cur.close()
            conn.close()
            return {"error": f"Application '{query_str}' not found."}

        app_id, app_no = row
        cur.execute("SELECT at, action, actor, note FROM audit_log WHERE application_id = %s ORDER BY at ASC", (app_id,))
        records = cur.fetchall()
        cur.close()
        conn.close()

        return {
            "application_id": app_id,
            "application_no": app_no,
            "total_events": len(records),
            "events": [
                {
                    "timestamp": r[0].strftime("%Y-%m-%d %H:%M:%S") if r[0] else "",
                    "action": r[1],
                    "actor": r[2],
                    "note": r[3] or ""
                }
                for r in records
            ]
        }
    except Exception as e:
        logger.error("Error reviewing audit trail: %s", e)
        return {"error": f"Failed to review audit trail: {str(e)}"}


@officer_server.tool()
def decide_application(
    application_id_or_no: str,
    decision: str,
    note: str,
    officer_username: Optional[str] = "admin"
) -> Dict[str, Any]:
    """
    Record an official administrative decision (APPROVED or REJECTED) on a PENDING pension application.
    Under state governance rules, a descriptive justification note is MANDATORY and will be permanently
    logged in the audit trail against the officer's name. An SMS alert is dispatched to the citizen.

    Args:
        application_id_or_no: Numeric ID (e.g. '100001') or application number (e.g. 'SSP26123456').
        decision: Must be strictly 'APPROVED' or 'REJECTED'.
        note: Mandatory justification or rationale (e.g. 'Verified age proof document matches DOB; residential verification confirmed by village head').
        officer_username: Username of the deciding officer (defaults to 'admin').
    """
    clean_decision = (decision or "").strip().upper()
    if clean_decision not in ("APPROVED", "REJECTED"):
        return {"success": False, "error": "Decision must be strictly 'APPROVED' or 'REJECTED'."}

    clean_note = (note or "").strip()
    if not clean_note or len(clean_note) < 5:
        return {
            "success": False,
            "error": "A substantive justification note (minimum 5 characters) is required for state audit compliance."
        }

    query_str = str(application_id_or_no).strip()
    officer_actor = f"officer:{officer_username or 'admin'}"

    try:
        conn = portal.get_db()
        cur = conn.cursor()

        # Check existing status
        if query_str.isdigit():
            cur.execute("SELECT id, application_no, mobile, status FROM applications WHERE id = %s", (int(query_str),))
        elif query_str.upper().startswith("SSP"):
            cur.execute("SELECT id, application_no, mobile, status FROM applications WHERE application_no = %s", (query_str,))
        else:
            cur.execute("SELECT id, application_no, mobile, status FROM applications WHERE application_no = %s OR applicant_name ILIKE %s ORDER BY id DESC LIMIT 1",
                        (query_str, f"%{query_str}%"))
        
        row = cur.fetchone()
        if not row:
            cur.close()
            conn.close()
            return {"success": False, "error": f"Application '{query_str}' not found."}

        app_id, app_no, mobile, current_status = row
        if current_status != "PENDING":
            cur.close()
            conn.close()
            return {
                "success": False,
                "error": f"Cannot decide application {app_no}: current status is '{current_status}'. Only PENDING applications can be decided."
            }

        decided_time = datetime.now()
        # Update application in database
        cur.execute(
            """UPDATE applications
               SET status = %s, decided_at = %s, decided_by = %s
               WHERE id = %s AND status = 'PENDING'
               RETURNING application_no""",
            (clean_decision, decided_time, officer_actor, app_id)
        )
        updated_row = cur.fetchone()
        if not updated_row:
            cur.close()
            conn.close()
            return {"success": False, "error": "Failed to update application; it may have been concurrently modified."}

        # Write to audit log
        portal.write_audit(cur, app_id, clean_decision, officer_actor, clean_note)
        conn.commit()
        cur.close()
        conn.close()

        # Send official SMS notification to applicant
        sms_text = f"Sewa Setu: your pension application {app_no} has been {clean_decision}. Decided by: {officer_username}."
        portal.send_sms(mobile, sms_text)

        return {
            "success": True,
            "application_id": app_id,
            "application_no": app_no,
            "previous_status": "PENDING",
            "new_status": clean_decision,
            "decided_by": officer_actor,
            "decided_at": decided_time.strftime("%Y-%m-%d %H:%M:%S"),
            "audit_note_recorded": clean_note,
            "sms_notified_to": f"XXXXXX{mobile[-4:]}",
            "message": f"Application {app_no} has been successfully {clean_decision.lower()} and recorded against {officer_actor}."
        }
    except Exception as e:
        logger.error("Error deciding application: %s", e)
        return {"success": False, "error": f"Database error during decision: {str(e)}"}
