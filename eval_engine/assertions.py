# -*- coding: utf-8 -*-
"""
Database Assertions for Sewa Setu Evaluation Suite.
Directly queries PostgreSQL to verify actual state changes post-conversation.
"""

import os
import sys
import logging
from typing import Dict, Any, List

APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app"))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

import app as portal

logger = logging.getLogger("sewasetu.eval.assertions")


def verify_database_assertion(assertion: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a strict database assertion against PostgreSQL.
    Returns: { "passed": bool, "description": str, "actual": Any, "expected": Any, "details": str }
    """
    assert_type = assertion.get("type")
    conn = portal.get_db()
    cur = conn.cursor()

    try:
        if assert_type == "EXISTS":
            table = assertion["table"]
            field = assertion["field"]
            val = assertion["value"]
            cur.execute(f"SELECT count(*) FROM {table} WHERE {field} = %s", (val,))
            count = cur.fetchone()[0]
            passed = count > 0
            return {
                "passed": passed,
                "assertion_type": assert_type,
                "description": f"Record exists in '{table}' where {field} = '{val}'",
                "actual": f"{count} record(s) found",
                "expected": "> 0 records"
            }

        elif assert_type == "NOT_EXISTS":
            table = assertion["table"]
            field = assertion["field"]
            val = assertion["value"]
            cur.execute(f"SELECT count(*) FROM {table} WHERE {field} = %s", (val,))
            count = cur.fetchone()[0]
            passed = (count == 0)
            return {
                "passed": passed,
                "assertion_type": assert_type,
                "description": f"No record exists in '{table}' where {field} = '{val}'",
                "actual": f"{count} records found",
                "expected": "0 records"
            }

        elif assert_type == "EQUALS":
            table = assertion["table"]
            field = assertion["field"]
            val = assertion["value"]
            target_field = assertion.get("target_field", field)
            expected = assertion.get("expected", val)
            
            cur.execute(f"SELECT {target_field} FROM {table} WHERE {field} = %s ORDER BY id DESC LIMIT 1", (val,))
            row = cur.fetchone()
            actual = row[0] if row else None
            passed = (actual == expected)
            return {
                "passed": passed,
                "assertion_type": assert_type,
                "description": f"Field '{target_field}' equals '{expected}' for {field}='{val}'",
                "actual": str(actual),
                "expected": str(expected)
            }

        elif assert_type == "COUNT_EQUALS":
            table = assertion["table"]
            field = assertion["field"]
            val = assertion["value"]
            expected_count = assertion["expected_count"]
            cur.execute(f"SELECT count(*) FROM {table} WHERE {field} = %s", (val,))
            count = cur.fetchone()[0]
            passed = (count == expected_count)
            return {
                "passed": passed,
                "assertion_type": assert_type,
                "description": f"Count of records in '{table}' where {field}='{val}' equals {expected_count}",
                "actual": count,
                "expected": expected_count
            }

        elif assert_type == "MIN_AGE":
            dob_str = assertion["dob"]
            min_age = assertion["min_age"]
            parsed_dob = portal.parse_dob(dob_str)
            age = portal.age_on(parsed_dob, portal.now_ist().date())
            passed = age >= min_age
            return {
                "passed": passed,
                "assertion_type": assert_type,
                "description": f"Age computed from DOB {dob_str} is >= {min_age}",
                "actual": f"{age} years",
                "expected": f">= {min_age} years"
            }

        elif assert_type == "AUDIT_LOG_ACTION":
            action = assertion["action"]
            cur.execute("SELECT id, application_id, actor, at FROM audit_log WHERE action = %s ORDER BY id DESC LIMIT 1", (action,))
            row = cur.fetchone()
            passed = bool(row)
            return {
                "passed": passed,
                "assertion_type": assert_type,
                "description": f"Audit trail contains action '{action}'",
                "actual": f"Audit entry #{row[0]} by {row[2]}" if row else "None",
                "expected": f"Action '{action}' present"
            }

        elif assert_type == "AUDIT_NOTE_CONTAINS":
            snippet = assertion["snippet"]
            cur.execute("SELECT count(*) FROM audit_log WHERE note ILIKE %s", (f"%{snippet}%",))
            count = cur.fetchone()[0]
            passed = count > 0
            return {
                "passed": passed,
                "assertion_type": assert_type,
                "description": f"Audit trail notes contain justification snippet: '{snippet}'",
                "actual": f"{count} matching log entry/entries",
                "expected": "> 0 entries"
            }

        else:
            return {
                "passed": False,
                "assertion_type": assert_type,
                "description": f"Unknown assertion type '{assert_type}'",
                "actual": "Unknown",
                "expected": "Known"
            }

    except Exception as e:
        logger.error("Assertion error: %s", e)
        return {
            "passed": False,
            "assertion_type": assert_type,
            "description": f"Database query failed: {str(e)}",
            "actual": "Error",
            "expected": "Success"
        }
    finally:
        cur.close()
        conn.close()
