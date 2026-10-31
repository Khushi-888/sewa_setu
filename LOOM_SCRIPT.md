# Sewa Setu: 3-Minute Loom Presentation & Walkthrough Script

**Presenter:** Senior AI Researcher & Build for Bharat AI Fellow  
**Audience:** Director of Social Welfare (IAS Officer) & Assessment Committee  
**Format:** 3 Minutes Max | Face Camera in Corner + Screen Recording  
**Theme:** Re-imagining Welfare Services in an Agentic World  

---

## [0:00 - 0:35] Part 1: The Core Problem & What We Achieved
**[Visual: Face cam speaking, transitioning to Sewa Setu Home Portal (`/`)]**

> "Namaskar Director Ma'am. When you shared the story of the 70-year-old grandmother from Sonari block whose grandson tried to apply for her ₹250 pension using an AI assistant on the bus and failed, the mission became crystal clear. 
> 
> General AI assistants hallucinate rules and cannot talk to government databases. Today, I am proud to present our solution: we have transformed Sewa Setu into a fully agentic welfare platform powered by **two streamable HTTP Model Context Protocol (MCP) servers**—one for citizens, and one for block officers. 
> 
> The portal remains the immutable system of record, while any modern AI assistant—like Claude Code or ChatGPT—can now guide an elderly citizen through mobile verification, eligibility checks, application submission, and statutory tracking."

---

## [0:35 - 1:25] Part 2: Architectural Design Decisions Across the Two MCPs
**[Visual: Architecture diagram from `ARCHITECTURE_AND_EVAL_DESIGN.md`, then showing endpoints in action]**

> "We made three pivotal architectural decisions:
> 
> **First: Cryptographic Security & Endpoint Isolation.** A citizen's assistant connecting to `/mcp/citizen` cannot even see officer tools. We anchored authorization in Sewa Setu's native OAuth 2.1 server with PKCE and RS256 JWT tokens. A citizen token presented at `/mcp/officer` is immediately blocked with an HTTP 403 Forbidden.
> 
> **Second: Single Source of Truth & Validation Parity.** Our MCP servers do not reinvent logic; every tool executes through the canonical `validate_application()` function. It enforces the statutory 60-year age limit calculated against Indian Standard Time, validates 9-to-18 digit bank accounts with 11-digit IFSC codes, respects the single-active-application rule for shared kiosk phones, and tracks the 15-day Right to Public Services statutory SLA.
> 
> **Third: Officer Queue Intelligence.** For the block officers, our Officer MCP prioritizes pending applications nearing the 15-day deemed approval deadline, pulls full applicant dossiers with document links, and mandates an administrative justification note before recording any approval or rejection."

---

## [1:25 - 2:25] Part 3: Live Walkthrough of `/eval-dashboard` & Our Personas
**[Visual: Screen shares `/eval-dashboard` on live deployment, clicking through personas and clicking "Run Live Evaluation"]**

> "We didn't just build the tools; we tested them against real humans in our evaluation suite at `/eval-dashboard`.
> 
> Here on the dashboard, you see our 6 realistic personas:
> - **Tileswari Gogoi (Age 71, Sonari):** Applied via her grandson's phone. Our agent validated her age, accepted her State Bank of India account, and lodged application `SSP26123456`.
> - **Haren Bora (Age 57, Rajapara):** Underage boundary test. The assistant politely informed him of the 60-year statutory threshold and refused submission without polluting the portal database.
> - **Golapi Rajkhowa (Age 68, Khelua):** Already holds an approved application. The assistant queried her status and prevented a duplicate submission.
> - **Deben Hazarika (Age 64, Borgaon):** Self-corrected an incomplete IFSC code and succeeded.
> - **Smti. Aruna Sharma (BDO Sonari):** Logged into the Officer MCP, inspected Tileswari's dossier, verified her age proof, and approved her pension with the mandatory recorded note: *'Physical verification corroborated with Gaonburah certificate.'*
> 
> Notice the assertion table below: our eval harness connects directly to PostgreSQL and verifies that every single field, status transition, and audit log row is 100% true in the database."

---

## [2:25 - 3:00] Part 4: What We Learned & The Path Forward
**[Visual: Highlighting the "What Our Evals Found" panel, then returning to full-screen / face cam]**

> "What did our evals teach us?
> 1. In rural blocks, shared phones are standard. Proactive active-application checks prevent family phone lockouts.
> 2. Small-screen bank account typos can be resolved in a single turn with instant regex feedback.
> 3. Officer accountability improves when approval notes are permanently stamped into the immutable audit trail.
> 
> With more time, we would build native multimodal voice streaming directly over MCP, allowing illiterate seniors to dial a toll-free number from basic feature phones in Assamese or Bengali.
> 
> Our deployment is live, all tests pass with 100% database verification, and the service is ready for your team's Claude Code test client. Thank you!"

---

## Technical Recording Checklist:
- [x] Resolution: 1080p, clear audio
- [x] Time: Exactly 2:50 - 3:00 minutes
- [x] Links demonstrated: `/`, `/eval-dashboard`, `/admin`, `/mcp/citizen`, `/mcp/officer`
- [x] Live click on "Run Live Evaluation Suite" showing badges turning green.
