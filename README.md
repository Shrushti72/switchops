# SwitchOps — AI-Powered Incident Response in Team Chat

<p align="center">
  <img src="https://img.shields.io/badge/Hackathon-Flip%20the%20Switch%202026-blueviolet?style=for-the-badge" alt="Hackathon" />
  <img src="https://img.shields.io/badge/Track-01%3A%20Best%20Business%20Workflow-success?style=for-the-badge" alt="Track" />
  <img src="https://img.shields.io/badge/Platform-Switch%20Protocol-orange?style=for-the-badge" alt="Switch" />
  <img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License" />
</p>

> **Flip the Switch Hackathon 2026 Submission** — Track 01: Best Business Workflow ($2,000)

SwitchOps brings AI coding agents directly into your team's chat channel (Mattermost, Slack, Discord, or Microsoft Teams) via [Switch](https://github.com/sandbox-quantum/switch). 

When a production incident occurs, the agents collaborate in real time to diagnose root causes, propose verifiable remediations, and **strictly enforce human sign-off (`APPROVE`)** before taking any operational action.

**Real incidents, diagnosed and resolved in chat. Humans stay firmly in control.**

---

## 📺 Demo Video

> 🎥 **[Watch the 2-Minute SwitchOps Demo Walkthrough](https://youtu.be/placeholder)** *(Recording linked during hackathon submission)*

---

## ⚖️ How SwitchOps Maps to the Judging Criteria

| Hackathon Criterion | Weight | How SwitchOps Delivers |
|---|---|---|
| **Use of Switch** | **30%** | **Central to the entire system.** Switch connects the team chat room to two specialized agents (`switchops-radar` & `switchops-ops`) via SSE/HTTP. Without Switch, agents have no shared context, cannot message each other, and cannot reach human engineers. |
| **Technical Execution** | **25%** | **Production-grade & reproducible.** Multi-agent orchestration, automated tool execution (log inspection & rollback), strict state machine enforcement (`APPROVE`), and zero-config local reproduction via Docker Compose. |
| **Creativity & Impact** | **25%** | **Addresses the #1 pain point in engineering:** on-call burnout and high MTTR. Matches the hackathon benchmark scenario 1:1, transforming chaos into an auditable, collaborative workflow. |
| **Presentation** | **20%** | **Comprehensive documentation:** clear architecture diagrams, reproducible quick-start guides, and automated postmortems. |

---

## 🎬 Live Incident Flow

```text
🚨 [Alert Simulator] 
   ALERT: cart-service error rate spiked to 94.2% (threshold: 5.0%) at 09:42 UTC.
   Deploy v2.14.0 was released at 09:40 UTC. @switchops-radar please investigate.

🔍 [switchops-radar BOT]
   The timing strongly points to v2.14.0 as the trigger: cart-service error rate 
   reached 94.2% two minutes after release. 
   Recommendation: Roll back to v2.13.2. 
   ⚠️ Ops should execute ONLY after a human posts APPROVE here.

👤 [Human Engineer]
   APPROVE

🤖 [switchops-radar BOT]
   @switchops-ops Human approval received in the channel. 
   Please execute the approved rollback to v2.13.2 and confirm completion here.

⚡ [switchops-ops BOT]
   Worked for 7s. 2 tool calls.
   ✅ Executed rollback: cart-service restored to v2.13.2.
   Health check: HTTP 200 OK
   Error rate: 0.1% (nominal)
   Incident resolved.

📋 [switchops-radar BOT]
   Cart-Service Incident Postmortem
   • Summary: Error spike mitigated, rollback to v2.13.2 verified (HTTP 200, 0.1% errors).
   • Timeline (UTC): 09:40 deploy -> 09:42 alert -> Human APPROVE -> Ops rollback.
   • Root Cause: v2.14.0 checkout regression.
   • Action Items: Inspect v2.14.0 logs/traces before re-deploying.
```

---

## 🏗️ Architecture

```text
                      ┌────────────────────────────────────────┐
                      │          Team Chat Channel             │
                      │             #incidents                 │
                      │                                        │
                      │  👤 Human On-Call Engineer             │
                      │  🔍 switchops-radar (Diagnosis Agent)  │
                      │  ⚡ switchops-ops   (Execution Agent)  │
                      └───────────────────┬────────────────────┘
                                          │
                            Switch Protocol (SSE in, HTTP out)
                                          │
                      ┌───────────────────▼────────────────────┐
                      │              Switch Core               │
                      │        (Switch Console Engine)         │
                      │                                        │
                      │  - Room Context Isolation              │
                      │  - Multi-Agent Orchestration           │
                      │  - Human-in-the-Loop Safety Gate       │
                      └───────────────────┬────────────────────┘
                                          │
               ┌──────────────────────────┼──────────────────────────┐
               ▼                          ▼                          ▼
      ┌─────────────────┐       ┌───────────────────┐      ┌───────────────────┐
      │  cart-service   │       │    log-server     │      │  alert-simulator  │
      │  (Docker)       │       │    (Docker)       │      │  (Docker)         │
      │                 │       │                   │      │                   │
      │  FAIL_RATE=0.0  │       │  GET /logs        │      │  Polls metrics    │
      │  → healthy      │       │  Returns recent   │      │  every 10s.       │
      │  FAIL_RATE=1.0  │       │  structured logs  │      │  Fires webhook    │
      │  → 500 incident │       │  with deploy info │      │  on threshold spike│
      └─────────────────┘       └───────────────────┘      └───────────────────┘
```

---

## 💡 Why Switch is Central

Without Switch, this workflow cannot exist:
1. **Shared Team Context**: Agents and humans share the exact same room timeline, rules, and history.
2. **Agent-to-Agent Coordination**: `switchops-radar` and `switchops-ops` communicate in-thread via Switch addressing.
3. **Strict Human Safety Gate**: `switchops-ops` listens to the channel but enforces human sign-off before executing any operational change.
4. **Platform Agnostic**: Works seamlessly whether the team uses Mattermost (zero-config local Docker), Slack, Discord, or Microsoft Teams.

---

## 🚀 Quick Start (One Command)

### Prerequisites
- [Switch Console](https://github.com/sandbox-quantum/switch/releases)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### 1. Load Room in Switch Console
* In Switch Console, click **File → Load Room Template** (or import `room.yaml`).
* Switch automatically configures `#incidents` with `switchops-radar` and `switchops-ops`.

### 2. Run the Demo Stack
```bash
docker compose up -d --build
```

### 3. Trigger an Incident
* **On Linux / macOS**:
  ```bash
  bash scripts/break-cart.sh
  ```
* **On Windows PowerShell**:
  ```powershell
  .\scripts\break-cart.ps1
  ```
*(Or post a simulated alert message directly into `#incidents`).*

### 4. Review & Resolve
1. Review `switchops-radar`'s root-cause analysis in chat.
2. Type **`APPROVE`** in `#incidents`.
3. Watch `switchops-ops` execute the rollback and verify recovery.
4. Request the postmortem: `@switchops-radar generate postmortem`.

---

## 📂 Project Structure

```text
switchops/
├── room.yaml                    # Switch room template (v2 declarative format)
├── docker-compose.yml           # Full demo services stack
├── README.md                    # Architecture and documentation
├── alert-simulator/             # Webhook service that monitors and triggers alerts
│   ├── main.py
│   └── Dockerfile
├── demo-services/
│   ├── cart-service/            # Simulated production service (degradable on demand)
│   │   ├── app.py
│   │   └── Dockerfile
│   └── log-server/              # Structured log emitter with deploy markers
│       ├── app.py
│       └── Dockerfile
└── scripts/
    ├── break-cart.sh            # Injects 500 error spike into cart-service (Bash)
    ├── break-cart.ps1           # Injects 500 error spike into cart-service (PowerShell)
    ├── fix-cart.sh              # Restores service to nominal state (Bash)
    └── fix-cart.ps1             # Restores service to nominal state (PowerShell)
```

---

## 🛠️ Built With

* **[Switch](https://github.com/sandbox-quantum/switch)** — Open-source agent collaboration infrastructure
* **AI Coding Agents** — Powered by OpenAI Codex / Antigravity via Switch Protocol
* **Mattermost / Slack** — Native team chat interfaces
* **FastAPI & Flask** — Microservice simulators
* **Docker Compose** — 100% reproducible local environment

---

## 📜 License

MIT License — free to use, modify, and reproduce.
