# Building SwitchOps: Autonomous, Zero-Downtime Incident Response in Team Chat via Switch

> *Submitted for the **Flip the Switch Hackathon 2026** (Track 01: Best Business Workflow & Best Tutorial Blog)*

---

## The 2:00 AM Production Nightmare

Every DevOps engineer knows the feeling: your phone rings at 2:14 AM. The checkout service error rate has just spiked to 94%.

In traditional setups, the next 45 minutes are pure chaos:
1. The on-call engineer wakes up and logs into the cloud console.
2. They open Datadog or Sentry to grep through thousands of unformatted logs.
3. They check Git commit logs to guess which deployment caused the regression.
4. Under extreme stress, they frantically run rollback commands on the CLI, hoping they don't fat-finger an option.

**Downtime costs thousands of dollars per minute. Manual triage is slow, stressful, and error-prone.**

What if your team chat was already an autonomous incident war room, where specialized AI agents collaborate with you to triage, stage fixes, and resolve outages in under 60 seconds—without ever acting without your explicit authorization?

Meet **SwitchOps**.

---

## What is SwitchOps?

SwitchOps brings AI coding agents directly into your team's chat channel (Mattermost, Slack, Discord, or Teams) using **[Switch](https://github.com/sandbox-quantum/switch)**.

Instead of a single chatbot that tries to do everything, SwitchOps implements a **Multi-Agent / Human-in-the-Loop Architecture** divided into two specialized roles:

1. **`switchops-radar` (The Triager & Diagnostic Agent):**
   * Listens for production alert webhooks in `#incidents`.
   * Queries and deep-dives into structured error logs using diagnostic tools (`scripts/inspect-logs.py`).
   * Correlates the error spike to the most recent deployment (`v2.14.0`).
   * Pinpoints the exact line causing the crash: `checkout.py:142 NullPointerException`.
   * Stages a rollback to `v2.13.2`, but **strictly halts** execution, demanding human sign-off (`APPROVE`).

2. **`switchops-ops` (The Operator & Execution Agent):**
   * Listens for human authorization in the channel.
   * **Never acts autonomously.** Only executes when it verifies a human `APPROVE` command in the Switch room log.
   * Runs the rollback script (`scripts/rollback.sh` / `scripts/rollback.ps1`), verifies the service health check (`HTTP 200 OK`), and confirms resolution in chat.

3. **Automated Incident Postmortem:**
   * Once uptime is nominal, Radar automatically drafts an official postmortem report covering the incident timeline, root cause analysis, and follow-up action items.

---

## System Architecture

```text
                      ┌────────────────────────────────────────┐
                      │          Team Chat Channel             │
                      │             #incidents                 │
                      │                                        │
                      │  👤 Human On-Call Engineer (Wispr Flow)│
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
                      │  - Room Context & State Persistence    │
                      │  - Multi-Agent Thread Addressing       │
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
      │  → 500 incident │       │  with stack trace │      │  on threshold spike│
      └─────────────────┘       └───────────────────┘      └───────────────────┘
```

---

## Why Switch is the Core Enabler

Many projects plug an LLM into Slack with a basic webhook. SwitchOps goes far beyond that because it leverages Switch's fundamental architectural superpowers:

### 1. State Persistence & Resilience
In a real incident, agents or network connections can hiccup. With Switch, every message, diagnostic step, and approval is persisted to an immutable room event log. If `switchops-ops` restarts mid-incident, it reads the room log, detects that human approval was already granted, and executes the recovery without forcing the engineer to start over.

### 2. Multi-Agent Addressing & Context Isolation
Switch allows `radar` and `ops` to operate with dedicated prompts, tools, and permission scopes while living in the same channel. Radar is scoped to `anyone` for active triage, while Ops is configured with `owner_and_owner_agents` addressing, ensuring it only responds to authorized commands.

### 3. Platform Portability
Thanks to Switch's bridge layer, the exact same `room.yaml` configuration runs seamlessly in Mattermost, Slack, Microsoft Teams, or Discord without changing a single line of agent logic.

---

## Voice-Activated DevOps with Wispr Flow

To eliminate operational friction under high-stress outages, SwitchOps pairs with **[Wispr Flow](https://flow.wispr.ai)**.

Instead of typing frantically on a keyboard, the on-call engineer reviews Radar's diagnostic card, presses `Ctrl + Win`, and speaks:
> *"APPROVE"*

Wispr Flow transcribes the approval instantly into the `#incidents` room, activating the execution agent hands-free.

---

## Step-by-Step Implementation Guide

Want to build your own Switch incident room? Here is how simple it is using declarative YAML:

### Step 1: The Switch Room Template (`room.yaml`)
```yaml
version: 2
name: "switchops-incident-response"
description: "Two-agent AI incident response room powered by Switch."

inputs:
  agent_provider:
    type: string
    default: "codex"
  bridge_app:
    type: string
    default: "mattermost"

resources:
  radar_agent:
    type: agent
    provider: "{inputs.agent_provider}"
    addressing: anyone
    instructions: |
      You are SwitchOps Radar. When an alert arrives:
      1. Acknowledge the alert.
      2. Inspect logs via: python ./scripts/inspect-logs.py <service>
      3. Correlate with recent deploys and isolate stack trace line.
      4. Post diagnosis proposing rollback to v2.13.2.
      5. Enforce human sign-off: DO NOT execute without APPROVE.
      6. Draft postmortem once fixed.

  ops_agent:
    type: agent
    provider: "{inputs.agent_provider}"
    addressing: owner_and_owner_agents
    instructions: |
      You are SwitchOps Ops.
      Execute fixes ONLY when human posts APPROVE.
      Rollback: bash ./scripts/rollback.sh <service> <version>
      Confirm with health check status.

  incidents_room:
    type: room
    bridge: "{inputs.bridge_app}"
    participants:
      - "{$creator}"
      - "{radar_agent.name}"
      - "{ops_agent.name}"
```

### Step 2: One-Command Local Reproduction
Clone the repository and start the full demo stack:
```bash
git clone https://github.com/YOUR_USERNAME/switchops.git
cd switchops
docker compose up -d --build
```

### Step 3: Trigger the Incident
Inject a 500 failure spike into the shopping cart microservice:
```powershell
.\scripts\break-cart.ps1
```
Watch both agents collaborate with you in real time in `#incidents`!

---

## Key Results & Business Impact

| Metric | Traditional Incident Response | SwitchOps with Switch |
|---|---|---|
| **Mean Time to Resolution (MTTR)** | 45 minutes | **< 60 seconds** |
| **Context Switching** | 4–6 tools (AWS, Datadog, Git, Slack) | **0 tools (All in team chat)** |
| **Safety & Governance** | High risk of manual human errors | **100% human-in-the-loop signoff** |
| **Auditability** | Scrambled notes & manual retro | **Immutable postmortem & room history** |

---

## Conclusion

AI in software engineering shouldn't just be an autocomplete tool inside a single developer's IDE. With **Switch**, AI becomes an active, transparent, and auditable teammate inside the collaboration tools where engineering teams already live.

Check out the full open-source codebase on GitHub: [SwitchOps Repository](https://github.com) 🚀
