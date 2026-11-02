# SwitchOps — AI-Powered Incident Response

> **Flip the Switch Hackathon 2026 submission** — Track 01: Best Business Workflow

SwitchOps puts two Antigravity AI agents into your team's Discord channel via [Switch](https://github.com/sandbox-quantum/switch). When production breaks, the agents diagnose the problem, propose a fix, and wait for a human to say **APPROVE** before touching anything.

**Real incidents, resolved in chat. Humans stay in control.**

---

## Demo

```
🚨 ALERT: cart-service error rate 94% since 09:42

⚡ [switchops-radar] Incident detected: cart-service 500 spike
   @switchops-ops please fetch last 50 logs for cart-service

📋 [switchops-ops] Here are the last 10 lines:
   2026-11-04T09:42:03Z ERROR [cart-service] NullPointerException in checkout
   2026-11-04T09:42:01Z INFO  [deploy-agent] Deployed v2.14.0 (was v2.13.2)
   ...

🔴 [switchops-radar] INCIDENT: cart-service
   ⏰ Started: 09:42 UTC
   📊 Error rate: 94% (normal: <1%)
   🔍 Root cause: v2.14.0 deployed at 09:40, null pointer in checkout handler
   🔧 Proposed fix: Rollback to v2.13.2
   ──────────────────────────────────
   Type APPROVE to execute or REJECT to escalate.

> [You] APPROVE

✅ [switchops-ops] Rolled back cart-service to v2.13.2.
   Error rate: 0.2% ✓

📋 [switchops-radar] Postmortem — cart-service — 2026-11-04
   • What happened: 500 spike to 94% after v2.14.0 deploy
   • Started at: 09:42 UTC, resolved 09:44 UTC (2 min MTTR)
   • Root cause: null pointer in checkout handler (v2.14.0)
   • Fix applied: rollback to v2.13.2 (approved by @you)
   • Action item: add null check before merging v2.14.0 again
```

---

## Architecture

```
                    ┌──────────────────────────────────┐
                    │         Discord Channel            │
                    │    #switchops-incidents            │
                    │                                    │
                    │  👤 You (human on-call)            │
                    │  🤖 switchops-radar (Antigravity)  │
                    │  🔧 switchops-ops   (Antigravity)  │
                    └──────────────┬───────────────────┘
                                   │ Switch bridges Discord ↔ agents
                    ┌──────────────▼───────────────────┐
                    │         Switch Core               │
                    │    (runs locally via Console)      │
                    │                                    │
                    │  SSE stream  ──► Agents            │
                    │  HTTP POST   ◄── Agents reply      │
                    └──────────────┬───────────────────┘
                                   │
          ┌────────────────────────┼────────────────────────┐
          ▼                        ▼                        ▼
  ┌───────────────┐   ┌────────────────────┐  ┌─────────────────────┐
  │  cart-service │   │    log-server      │  │  alert-simulator    │
  │  (Docker)     │   │    (Docker)        │  │  (Docker)           │
  │               │   │                    │  │                     │
  │  FAIL_RATE=0  │   │  GET /logs?service │  │  Polls cart every   │
  │  → healthy    │   │  Returns structured│  │  10s. Fires Switch  │
  │               │   │  logs with errors  │  │  webhook on spike.  │
  │  FAIL_RATE=1  │   │  highlighted       │  │                     │
  │  → incident   │   └────────────────────┘  └─────────────────────┘
  └───────────────┘
```

---

## Why Switch is Central

Without Switch, this workflow doesn't exist. Switch is what:
1. **Puts agents in the chat room** — without it, Antigravity can't see team messages
2. **Gives agents shared context** — both agents see the same incident thread
3. **Routes @mentions between agents** — Radar tells Ops to fetch logs via Switch
4. **Surfaces the APPROVE/REJECT gate** — the human's approval happens in Switch's room

Remove Switch and you have two agents that can't talk to anyone.

---

## Quick Start (5 minutes)

### Prerequisites
- [Switch Console](https://github.com/sandbox-quantum/switch/releases/latest/download/switch-console-x64.exe) (Windows)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- A Discord server (or Slack workspace)

### Step 1 — Set up Switch

1. Install Switch Console and open it
2. Talk to `switch-buddy`: *"Create two agents called switchops-radar and switchops-ops, connect them to Discord"*
3. Or load `room.yaml` directly via **File → Load Room Template**
4. Note your **Room ID** and **Webhook Token** from the Console

### Step 2 — Configure environment

```bash
cp .env.example .env
# Edit .env and fill in SWITCH_ROOM_ID and SWITCH_WEBHOOK_TOKEN
```

### Step 3 — Start the demo stack

```bash
docker compose up --build
```

This starts:
- `cart-service` on port 8001 (healthy by default)
- `log-server` on port 8080
- `alert-simulator` on port 9000 (polling every 10s)

### Step 4 — Trigger an incident

```bash
bash scripts/break-cart.sh
```

Watch your Discord channel — the alert fires in ~10 seconds and the agents take over.

### Step 5 — Approve the fix

When `switchops-radar` posts the diagnosis card, type **APPROVE** in Discord.

### Step 6 — Recover

```bash
bash scripts/fix-cart.sh
```

Or just type APPROVE in chat after the agents propose the rollback.

---

## Project Structure

```
switchops/
├── room.yaml                    # Switch room config (v2 format)
├── docker-compose.yml           # Full demo stack
├── .env.example                 # Config template
├── alert-simulator/
│   ├── main.py                  # FastAPI — polls cart, fires Switch webhooks
│   └── Dockerfile
├── demo-services/
│   ├── cart-service/
│   │   ├── app.py               # Flask — FAIL_RATE env var controls errors
│   │   └── Dockerfile
│   └── log-server/
│       ├── app.py               # Returns structured logs with error injection
│       └── Dockerfile
└── scripts/
    ├── break-cart.sh            # Triggers the incident
    └── fix-cart.sh              # Simulates rollback recovery
```

---

## How the Agents Work

### switchops-radar (Incident Radar)
- **Addressing:** `anyone` — responds to any message in the room
- **Trigger:** Alert messages containing 🚨 or keywords like "error rate", "500", "timeout"
- **Actions:**
  1. Acknowledge + triage
  2. Request logs from ops
  3. Analyze + propose ONE fix
  4. Post structured diagnosis card
  5. Gate on human APPROVE/REJECT
  6. Write postmortem after resolution

### switchops-ops (Ops Executor)
- **Addressing:** `owner_and_owner_agents` — only responds to Radar + room owner
- **Actions:**
  1. Fetch logs from log-server when Radar asks
  2. Execute rollback/restart/scale ONLY after APPROVE relayed by Radar
  3. Post confirmation with output

---

## Built With

| Technology | Role |
|---|---|
| [Switch](https://github.com/sandbox-quantum/switch) | Connects agents to Discord; shared room context |
| [Antigravity](https://www.antigravity.ai) | AI agent powering both Radar and Ops |
| FastAPI + Flask | Alert simulator + demo microservices |
| Docker Compose | One-command reproducible environment |

---

## License

MIT — clone it, fork it, run it, ship it.
