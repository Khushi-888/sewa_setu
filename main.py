# -*- coding: utf-8 -*-
"""
Sewa Setu Unified ASGI Application.

Assembles:
  1. Streamable HTTP Citizen MCP Server (/mcp/citizen)
  2. Streamable HTTP Block Officer MCP Server (/mcp/officer)
  3. Interactive Evaluation Dashboard (/eval-dashboard, /api/eval/run)
  4. Core Sewa Setu Flask Portal & OAuth 2.1 Server (mounted via a2wsgi at /)
"""

import os
import sys
import json
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

# Ensure both root and app are on path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(BASE_DIR, "app")
for d in (BASE_DIR, APP_DIR):
    if d not in sys.path:
        sys.path.insert(0, d)

# Automatic host/container detection
is_docker = os.path.exists("/.dockerenv") or bool(os.environ.get("DOCKER_CONTAINER"))
os.environ.setdefault("DB_HOST", "db" if is_docker else "localhost")
os.environ.setdefault("SMS_GATEWAY_URL", "http://smsgw:8025" if is_docker else "http://localhost:8025")
os.environ.setdefault("UPLOAD_DIR", "/var/sewasetu/uploads" if is_docker else os.path.join(BASE_DIR, "uploads"))

# Auto-detect public tunnel URL if not explicitly set
if not os.environ.get("PUBLIC_BASE_URL"):
    try:
        import urllib.request
        with urllib.request.urlopen("http://127.0.0.1:4040/api/tunnels", timeout=1) as resp:
            data = json.loads(resp.read().decode())
            if data.get("tunnels"):
                os.environ["PUBLIC_BASE_URL"] = data["tunnels"][0]["public_url"]
                logger.info("Detected public tunnel base URL: %s", os.environ["PUBLIC_BASE_URL"])
    except Exception:
        pass

import app as portal
import oauth
from a2wsgi import WSGIMiddleware
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader

from mcp_servers.citizen_mcp import citizen_server
from mcp_servers.officer_mcp import officer_server
from mcp_servers.transport import RoleEnforcementMiddleware, handle_jsonrpc_request
from eval_engine.runner import run_all_evaluations, EVAL_RUN_CACHE

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("sewasetu.main")

# Jinja2 template loader for eval dashboard
template_env = Environment(loader=FileSystemLoader(os.path.join(APP_DIR, "templates")))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup initialization: bootstrap database if needed & pre-seed evaluations."""
    logger.info("Initializing Sewa Setu Agentic Platform...")
    try:
        from bootstrap import ensure_database_initialized
        ensure_database_initialized()
    except Exception as e:
        logger.warning("Database bootstrap warning: %s", e)

    try:
        # Pre-seed initial eval run so dashboard is populated immediately on startup
        logger.info("Running baseline persona evaluation suite...")
        await run_all_evaluations()
        logger.info("Baseline evaluations completed successfully. Pass rate: %s%%",
                    EVAL_RUN_CACHE["summary"]["pass_rate_pct"])
    except Exception as e:
        logger.warning("Initial eval warm-up warning (DB may still be starting): %s", e)
    yield
    logger.info("Shutting down Sewa Setu...")


app = FastAPI(
    title="Sewa Setu Agentic Welfare Platform",
    description="Streamable HTTP MCP Servers and Welfare Portal for Government of Purvanchal",
    version="1.0.0",
    lifespan=lifespan
)

# Apply security and role boundary middleware
app.add_middleware(RoleEnforcementMiddleware)


# ---------------------------------------------------------------------------
# Evaluation Dashboard Routes
# ---------------------------------------------------------------------------

@app.get("/eval-dashboard", response_class=HTMLResponse)
async def eval_dashboard(request: Request):
    """Interactive Evaluation Dashboard displaying personas, transcripts, and DB assertions."""
    # If cache is empty, run now
    if not EVAL_RUN_CACHE["results"]:
        await run_all_evaluations()

    tmpl = template_env.get_template("eval_dashboard.html")
    html_content = tmpl.render(
        summary=EVAL_RUN_CACHE["summary"],
        results=EVAL_RUN_CACHE["results"],
        timestamp=EVAL_RUN_CACHE["last_run_timestamp"]
    )
    return HTMLResponse(content=html_content)


@app.post("/api/eval/run")
async def trigger_eval_run():
    """Trigger live evaluation run across all 6 citizen and officer personas."""
    try:
        eval_output = await run_all_evaluations()
        return {
            "success": True,
            "timestamp": eval_output["timestamp"],
            "summary": eval_output["summary"]
        }
    except Exception as e:
        logger.error("Error during triggered evaluation: %s", e)
        return {"success": False, "error": str(e)}


@app.get("/api/eval/results")
async def get_eval_results():
    """JSON API to retrieve current evaluation results and assertions."""
    if not EVAL_RUN_CACHE["results"]:
        await run_all_evaluations()
    return EVAL_RUN_CACHE


# ---------------------------------------------------------------------------
# Built-in SMS Gateway Endpoints (PurvSMS Simulation)
# ---------------------------------------------------------------------------

@app.post("/api/send")
async def simulated_sms_send(request: Request):
    """Simulated telecom SMS gateway endpoint for single-process deployments."""
    try:
        data = await request.json()
    except Exception:
        data = {}
    to = data.get("to", "")
    text = data.get("text", "")
    if not to or not text:
        return JSONResponse(status_code=400, content={"status": "error", "reason": "to and text required"})
    
    from sms_hub import record_sms
    msg = record_sms(to, text)
    logger.info("PurvSMS In-Process Dispatch -> To: %s | Text: %s", to, text)
    return {"status": "queued", "id": msg["id"]}


@app.get("/api/messages")
async def simulated_sms_messages(to: str = ""):
    """Simulated telecom SMS inbox inspection endpoint."""
    from sms_hub import get_messages
    return {"messages": get_messages(to)}


@app.get("/sms-console", response_class=HTMLResponse)
async def sms_console():
    """Live web console for reviewing dispatched OTPs and applicant notifications."""
    import time
    from sms_hub import SMS_STORE
    now = time.time()
    rows = ""
    for m in reversed(SMS_STORE[-100:]):
        sent_hhmm = time.strftime("%H:%M:%S", time.localtime(m["sent_at"]))
        is_deliv = now >= m["delivery_at"]
        st_badge = '<span style="color:#15803d;font-weight:700;">Delivered</span>' if is_deliv else '<span style="color:#b45309;font-weight:700;">In Transit</span>'
        txt = m["text"] if is_deliv else '<i>(carrier latency...)</i>'
        rows += f"<tr><td>{m['id']}</td><td><code>{m['to']}</code></td><td>{txt}</td><td>{sent_hhmm}</td><td>{st_badge}</td></tr>"

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>PurvSMS Telecom Gateway Console</title>
  <meta http-equiv="refresh" content="5">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 24px; background: #f8fafc; color: #1e293b; }}
    .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }}
    h2 {{ margin: 0; color: #0f385c; }}
    .badge {{ background: #dcfce7; color: #166534; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
    th, td {{ padding: 12px 16px; text-align: left; border-bottom: 1px solid #e2e8f0; font-size: 13.5px; }}
    th {{ background: #f1f5f9; font-weight: 600; color: #475569; }}
    a {{ color: #2563eb; text-decoration: none; }}
  </style>
</head>
<body>
  <div class="header">
    <div>
      <h2>PurvSMS Telecom Gateway Console (Built-in Simulation)</h2>
      <p style="margin: 4px 0 0; color: #64748b; font-size: 13px;">Live telecom carrier feed for Sewa Setu pension OTPs & notifications &middot; Auto-refreshes every 5s</p>
    </div>
    <div>
      <span class="badge">&bull; Operational</span>
      <a href="/" style="margin-left: 12px; font-size: 13px;">&larr; Back to Portal</a>
    </div>
  </div>
  <table>
    <thead><tr><th>ID</th><th>Recipient Mobile</th><th>SMS Message Body</th><th>Sent Time (IST)</th><th>Status</th></tr></thead>
    <tbody>
      {rows or '<tr><td colspan="5" style="text-align:center;padding:32px;color:#94a3b8;">No SMS messages dispatched yet. Trigger an OTP on /apply to test.</td></tr>'}
    </tbody>
  </table>
</body>
</html>"""
    return HTMLResponse(content=html)


# ---------------------------------------------------------------------------
# Direct JSON-RPC 2.0 Streamable HTTP Fallbacks
# ---------------------------------------------------------------------------

@app.post("/mcp/citizen")
async def citizen_direct_rpc(request: Request):
    """Direct JSON-RPC 2.0 endpoint for Citizen MCP Server."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}})
    res = await handle_jsonrpc_request(citizen_server, body)
    return JSONResponse(content=res)


@app.post("/mcp/officer")
async def officer_direct_rpc(request: Request):
    """Direct JSON-RPC 2.0 endpoint for Officer MCP Server."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}})
    res = await handle_jsonrpc_request(officer_server, body)
    return JSONResponse(content=res)


# ---------------------------------------------------------------------------
# Mount Official MCP SSE Sub-Applications
# ---------------------------------------------------------------------------

citizen_sse_subapp = citizen_server.sse_app(sse_path="/sse", message_path="/messages/")
officer_sse_subapp = officer_server.sse_app(sse_path="/sse", message_path="/messages/")

app.mount("/mcp/citizen", citizen_sse_subapp)
app.mount("/mcp/officer", officer_sse_subapp)


# ---------------------------------------------------------------------------
# Mount Canonical Sewa Setu Flask Portal as System of Record
# ---------------------------------------------------------------------------

app.mount("/", WSGIMiddleware(portal.app))


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")
