# Deploying Sewa Setu Assistant to Render

This guide outlines how to deploy the **Sewa Setu Agentic Welfare Platform** to [Render](https://render.com) as a public, high-availability cloud deployment.

---

## Architecture on Render

```
                                      ┌─────────────────────────────────────┐
                                      │            Render PaaS              │
                                      │                                     │
   Citizen / Officer ── HTTPS ───────►│  Web Service (FastAPI + ASGI)       │
   (or LLM Agents via MCP)            │  - Streamable HTTP Citizen MCP      │
                                      │  - Streamable HTTP Officer MCP      │
                                      │  - Interactive /eval-dashboard      │
                                      │  - Canonical Portal (/admin, etc.)  │
                                      │  - Built-in PurvSMS Telecom Hub     │
                                      │                  │                  │
                                      │                  ▼                  │
                                      │  Managed PostgreSQL (sewasetu-db)   │
                                      │  - 100k Seeded Applications         │
                                      │  - Audit Logs & Statutory SLAs      │
                                      └─────────────────────────────────────┘
```

The system is architected for zero-friction deployment:
- **Unified ASGI Server**: Mounts official MCP streamable endpoints, evaluation engine, and canonical portal in a single process.
- **Built-in Telecom Hub**: Operates an in-memory/in-process SMS simulation with console at `/sms-console`, ensuring OTP verification works immediately without extra worker processes.
- **Automatic Database Bootstrapper**: On initial boot, if the PostgreSQL database is empty, the application automatically applies `app/schema.sql` and streams the full ~100k record baseline dataset (`seed/seed.sql`).

---

## Method 1: 1-Click Blueprint Deployment (Recommended)

Render Blueprints read `render.yaml` directly from your Git repository and automatically provision both the **Web Service** and the **Managed PostgreSQL Database**.

### Step 1: Push Repository to GitHub
Ensure your repository is pushed to your GitHub account (e.g. `https://github.com/your-username/sewasetu-assistant`).

### Step 2: Create Blueprint on Render
1. Log in to your [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** in the top navigation bar and select **Blueprint**.
3. Connect your GitHub repository (`sewasetu-assistant`).
4. Render will detect `render.yaml` and configure:
   - **Database**: `sewasetu-db` (PostgreSQL 16/18)
   - **Web Service**: `sewasetu-assistant` (Python 3.11)
   - **Environment Variables**: Automatic linking of `DATABASE_URL`, `ADMIN_USERNAME=admin`, `ADMIN_PASSWORD=admin123`.
5. Click **Apply**.
6. Render will provision the database and build the web service.

---

## Method 2: Manual Setup via Render Dashboard

If you prefer configuring services manually via the Render UI:

### Step 1: Provision Managed PostgreSQL
1. On Render Dashboard, click **New +** &rarr; **PostgreSQL**.
2. **Name**: `sewasetu-db`
3. **Database**: `sewasetu`
4. **User**: `sewasetu`
5. **Region**: Oregon (or nearest region)
6. **Plan**: Free
7. Click **Create Database**.
8. Once created, copy the **Internal Database URL** (e.g. `postgres://sewasetu:...@dpg-...-a/sewasetu`).

### Step 2: Deploy Web Service
1. Click **New +** &rarr; **Web Service**.
2. Connect your Git repository (`sewasetu-assistant`).
3. Fill in the service configuration:
   - **Name**: `sewasetu-assistant`
   - **Region**: Same region as your database (e.g. Oregon)
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free
4. Under **Environment Variables**, add:
   | Key | Value | Description |
   |---|---|---|
   | `DATABASE_URL` | *(Paste Internal Database URL from Step 1)* | PostgreSQL connection string |
   | `PYTHON_VERSION` | `3.11.9` | Recommended Python runtime |
   | `ADMIN_USERNAME` | `admin` | Required officer username |
   | `ADMIN_PASSWORD` | `admin123` | Required officer password |
   | `SECRET_KEY` | *(Click Generate or enter secret)* | Flask/FastAPI session secret |
   | `PUBLIC_BASE_URL`| `https://<your-render-subdomain>.onrender.com` | Public domain for OAuth metadata |
5. Click **Deploy Web Service**.

---

## Verification & Health Check

Once the deployment finishes and shows **Live**:

### 1. Public Portal
Visit your Render URL:
```
https://<your-service>.onrender.com/
```
Verify the homepage loads with live statistics (Total Applications: ~100k+, Approved, Pending, Deemed Approved), the 5-second eligibility checker, and the interactive AI assistant widget.

### 2. Officer Login
Visit:
```
https://<your-service>.onrender.com/admin
```
- **Username**: `admin`
- **Password**: `admin123`
Verify you are redirected to `/admin/dashboard` showing pending workload and queue breakdown.

### 3. Evaluation Dashboard
Visit:
```
https://<your-service>.onrender.com/eval-dashboard
```
Verify:
- 6 personas evaluated across 16 database assertions.
- 100% pass rate.
- Multi-turn conversational transcripts and direct SQL assertion proofs.
- Click **"Run Full Evaluation Suite"** to verify live on-demand execution.

### 4. Official MCP Streamable Endpoints
Verify streamable HTTP MCP discovery:
```bash
# Citizen MCP Server discovery
curl -X POST https://<your-service>.onrender.com/mcp/citizen \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}'

# Officer MCP Server discovery
curl -X POST https://<your-service>.onrender.com/mcp/officer \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}'
```

### 5. PurvSMS Live Console
Visit:
```
https://<your-service>.onrender.com/sms-console
```
Inspect real-time telecom SMS dispatches and OTP codes.
