# -*- coding: utf-8 -*-
"""End-to-end evaluation suite test across all personas and live database assertions."""

import os
import sys
import asyncio

APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app"))
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for d in (ROOT_DIR, APP_DIR):
    if d not in sys.path:
        sys.path.insert(0, d)

os.environ["DB_HOST"] = os.environ.get("DB_HOST", "localhost")
os.environ["SMS_GATEWAY_URL"] = os.environ.get("SMS_GATEWAY_URL", "http://localhost:8025")

from eval_engine.runner import run_all_evaluations


async def main():
    print("Executing complete persona evaluation suite against Sewa Setu...")
    output = await run_all_evaluations()
    summary = output["summary"]
    print(f"\n--- EVALUATION SUMMARY ---")
    print(f"Total Personas Evaluated: {summary['total_personas']}")
    print(f"Personas Passed:          {summary['passed']}")
    print(f"Pass Rate:                {summary['pass_rate_pct']}%")
    print(f"Total DB Assertions:      {summary['total_assertions']}")
    print(f"Assertions Passed:        {summary['assertions_passed']}")
    print(f"Assertions Pass Rate:     {summary['assertions_pass_rate_pct']}%\n")

    for res in output["results"]:
        status = "PASSED" if res["passed"] else "FAILED"
        print(f"[{status}] {res['persona_name']} ({res['role']}) - {res['duration_seconds']}s")
        for a in res["assertions"]:
            mark = "OK" if a["passed"] else "FAIL"
            print(f"    [{mark}] {a['description']} (actual: {a['actual']})")

    assert summary["passed"] == summary["total_personas"], "All personas must pass!"
    assert summary["assertions_passed"] == summary["total_assertions"], "All DB assertions must pass!"
    print("\n[SUCCESS] 100% Evaluation and Database Assertion Verification Achieved!")


if __name__ == "__main__":
    asyncio.run(main())
