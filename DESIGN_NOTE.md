# Sewa Setu: Architecture & Design Decisions
**Author:** Bharat AI Fellow, Department of Social Welfare, Government of Purvanchal  
**Deliverable:** Build for Bharat Technical Submission & Assessment  

---

## 1. Executive Context
The Sewa Setu Old Age Pension Scheme delivers a monthly subsistence of ₹250 to over 100,000 vulnerable senior citizens (aged 60+) across Purvanchal. Re-imagining this service for an agentic world requires moving beyond conversational wrappers to structural protocol integration. We developed two separate Model Context Protocol (MCP) servers over Streamable HTTP: one for citizens/applicants (`scope: citizen`) and one for block development officers (`scope: officer`), maintaining Sewa Setu as the immutable system of record.

---

## 2. The Three Decisions That Mattered Most

### Decision 1: Cryptographic Endpoint Isolation & Strict Role Boundary Separation
* **The Problem:** A single unified assistant or blended endpoint creates severe privilege leakage risks. If a citizen's conversational agent can discover or invoke administrative tools (e.g., `decide_application`), prompt injections or unintended tool selection could grant unauthorized approvals.
* **Our Decision:** We separated the architecture into two distinct Streamable HTTP endpoints: `/mcp/citizen` and `/mcp/officer`. A citizen's assistant connecting to `/mcp/citizen` cannot even discover officer tools (`tools/list` omits them entirely). Furthermore, we anchored authorization in Sewa Setu's native OAuth 2.1 authorization server (RFC 8414, RFC 7591, PKCE S256, and RFC 8707 Resource Indicators). The Officer MCP server cryptographically verifies incoming RS256 JWT access tokens against the portal's JWKS (`/.well-known/jwks.json`). A citizen token presented at `/mcp/officer` is rejected with an HTTP 403 Forbidden.
* **Why It Mattered:** It guarantees zero administrative privilege escalation while allowing third-party AI assistants (Claude Code, ChatGPT, open-source agents) to interoperate safely using open standards.

### Decision 2: The Portal as the Immutable System of Record with Canonical Validation Parity
* **The Problem:** AI agents are prone to hallucinating rules, accepting underage applicants, skipping bank format checks, or generating ghost entries that bypass state statutory procedures.
* **Our Decision:** The AI assistant is strictly a channel, never the decision-maker of record. All MCP tool calls execute through the canonical portal validator `validate_application()` and persistence logic `create_application()`. Every rule enforced at the physical counter is enforced identically by the agent:
  1. Statutory age $\ge 60$ years calculated against Indian Standard Time (IST).
  2. Single active application constraint per mobile number (protecting shared kiosk phones).
  3. Strict 9–18 digit bank account and 11-character alphanumeric IFSC format (`[A-Z]{4}0[A-Z0-9]{6}`).
  4. Mandatory age-proof document linkage.
  5. Immutable audit logging (`audit_log`) and automated statutory SLA tracking (15-day deemed approval under the Purvanchal Right to Public Services Act).
* **Why It Mattered:** The assistant can never grant an applicant a pension that the counter or paper form would refuse, protecting departmental fiscal integrity while drastically cutting counter queues.

### Decision 3: Persona-Driven Evaluation Anchored in Live Database Truth
* **The Problem:** Evaluating LLM applications solely on conversational fluency or text outputs is deceptive; a model can produce a polite, convincing confirmation message while silently failing to commit the transaction to the database or failing field validation.
* **Our Decision:** We designed a rigorous evaluation framework based on 6 realistic personas reflecting rural realities (elderly widows, illiterate applicants sharing relatives' phones, underage farmers, citizens with active duplicate applications, applicants with bank typos, and overloaded block development officers). We built an interactive `/eval-dashboard` that runs multi-turn conversations through the real MCP streamable HTTP client and performs direct SQL assertions against PostgreSQL post-conversation (verifying record insertion, field normalization, status transitions, and audit logs).
* **Why It Mattered:** It guarantees 100% database fidelity. Our evals caught subtle edge cases (e.g., grandson's shared phone blocking duplicate submission, small-screen IFSC typos) that informed our defensive tool design.

---

## 3. The One Decision We Would Make Differently With More Time

### Native Multimodal Voice & Telephony Streaming over MCP
* **What We Implemented:** We implemented Streamable HTTP / Server-Sent Events (SSE) and JSON-RPC 2.0 endpoints catering to text-based AI clients, smartphones, and web kiosks.
* **What We Would Do Differently:** If given another iteration, we would build native **voice streaming and Interactive Voice Response (IVR) telephony integration** directly into the Citizen MCP pipeline (e.g., WebRTC / SIP integration with regional speech-to-text models for Assamese and Bengali). 
* **The Strategic Justification:** In rural Purvanchal, many senior citizens like 71-year-old Tileswari Gogoi are illiterate and lack smartphones; they rely entirely on family members or travel miles to Common Service Center (CSC) kiosks. A direct voice channel where an elderly citizen can dial a state toll-free number from a basic ₹1,000 feature phone, speak in her native dialect, receive conversational audio assistance, and have the agent drive the MCP tool calls in real time would dismantle the final digital divide in public welfare delivery.
