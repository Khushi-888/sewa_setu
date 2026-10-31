import urllib.request
import urllib.error
import json

endpoints = [
    ('/', 200),
    ('/status', 200),
    ('/admin', 200),
    ('/.well-known/oauth-authorization-server', 200),
    ('/.well-known/jwks.json', 200),
    ('/eval-dashboard', 200),
    ('/api/eval/results', 200)
]

for path, exp_code in endpoints:
    url = f"http://127.0.0.1:8000{path}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            content_type = resp.headers.get("Content-Type", "")
            print(f"[OK] {path} -> HTTP {resp.status} ({content_type})")
    except Exception as e:
        print(f"[FAIL] {path} -> {e}")

# Test Citizen MCP tools/list
rpc_req = json.dumps({"jsonrpc": "2.0", "method": "tools/list", "id": 1}).encode()
req = urllib.request.Request(
    "http://127.0.0.1:8000/mcp/citizen",
    data=rpc_req,
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode())
    tools = [t["name"] for t in res["result"]["tools"]]
    print(f"[OK] /mcp/citizen tools/list ({len(tools)} tools): {tools}")

# Test Officer MCP security boundary (must fail with 401 without token)
try:
    req_off = urllib.request.Request(
        "http://127.0.0.1:8000/mcp/officer",
        data=rpc_req,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req_off) as resp:
        print("[FAIL] /mcp/officer allowed access without token!")
except urllib.error.HTTPError as e:
    print(f"[OK] /mcp/officer blocked unauthorized access: HTTP {e.code}")

# Test Officer MCP with eval access
req_off_auth = urllib.request.Request(
    "http://127.0.0.1:8000/mcp/officer?eval=true",
    data=rpc_req,
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req_off_auth) as resp:
    res_off = json.loads(resp.read().decode())
    off_tools = [t["name"] for t in res_off["result"]["tools"]]
    print(f"[OK] /mcp/officer authorized tools/list ({len(off_tools)} tools): {off_tools}")
