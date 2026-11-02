"""
SwitchOps Alert Simulator
─────────────────────────
Polls cart-service every N seconds. When error rate exceeds threshold,
fires a webhook message to Switch Core so the Radar agent picks it up.
"""

import asyncio
import json
import os
import time
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="SwitchOps Alert Simulator")

# ── Config ────────────────────────────────────────────────────────────────
CART_URL = os.getenv("CART_SERVICE_URL", "http://cart-service:8001")
SWITCH_CORE_URL = os.getenv("SWITCH_CORE_URL", "http://host.docker.internal:2468")
SWITCH_TOKEN = os.getenv("SWITCH_WEBHOOK_TOKEN", "")
SWITCH_ROOM_ID = os.getenv("SWITCH_ROOM_ID", "")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL_SECONDS", "10"))
THRESHOLD = float(os.getenv("ERROR_THRESHOLD", "0.05"))  # 5%

# ── State ─────────────────────────────────────────────────────────────────
alert_fired = False
alert_fired_at: datetime | None = None
error_rate_history: list[dict] = []


async def check_cart_health() -> dict:
    """Poll cart-service /metrics endpoint for current error rate."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{CART_URL}/metrics")
            return r.json()
    except Exception as e:
        return {"error_rate": 1.0, "total_requests": 0, "error": str(e)}


async def fire_switch_alert(error_rate: float, service_version: str):
    """POST an alert message to Switch Core room webhook."""
    now = datetime.now(timezone.utc).strftime("%H:%M UTC")
    pct = f"{error_rate * 100:.1f}"

    message = (
        f"🚨 **ALERT: cart-service**\n"
        f"Error rate has spiked to **{pct}%** (threshold: {THRESHOLD*100:.0f}%)\n"
        f"Service version: `{service_version}`\n"
        f"Detected at: {now}\n\n"
        f"@switchops-radar please investigate."
    )

    headers = {
        "Authorization": f"Bearer {SWITCH_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {"text": message}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                f"{SWITCH_CORE_URL}/ap/v1/rooms/{SWITCH_ROOM_ID}/messages",
                headers=headers,
                json=payload,
            )
            print(f"[alert-sim] Alert fired → {r.status_code}: {r.text[:100]}")
            return r.status_code == 200
    except Exception as e:
        print(f"[alert-sim] Failed to fire alert: {e}")
        return False


async def recovery_notice():
    """Notify the room when cart-service recovers."""
    now = datetime.now(timezone.utc).strftime("%H:%M UTC")
    message = (
        f"✅ **RECOVERY: cart-service**\n"
        f"Error rate is back below threshold at {now}.\n"
        f"Incident auto-closed by SwitchOps Radar."
    )
    headers = {"Authorization": f"Bearer {SWITCH_TOKEN}", "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                f"{SWITCH_CORE_URL}/ap/v1/rooms/{SWITCH_ROOM_ID}/messages",
                headers=headers,
                json={"text": message},
            )
    except Exception as e:
        print(f"[alert-sim] Recovery notice failed: {e}")


async def monitor_loop():
    """Main monitoring loop — runs forever, fires alerts on threshold breach."""
    global alert_fired, alert_fired_at
    print(f"[alert-sim] Monitoring {CART_URL} every {POLL_INTERVAL}s (threshold={THRESHOLD*100}%)")

    while True:
        metrics = await check_cart_health()
        error_rate = metrics.get("error_rate", 0.0)
        version = metrics.get("version", "unknown")

        # Track history (keep last 30 samples)
        error_rate_history.append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "error_rate": error_rate,
        })
        if len(error_rate_history) > 30:
            error_rate_history.pop(0)

        print(f"[alert-sim] error_rate={error_rate:.2%}  alert_fired={alert_fired}")

        if error_rate > THRESHOLD and not alert_fired:
            print(f"[alert-sim] Threshold breached ({error_rate:.2%})! Firing alert.")
            fired = await fire_switch_alert(error_rate, version)
            if fired:
                alert_fired = True
                alert_fired_at = datetime.now(timezone.utc)

        elif error_rate <= THRESHOLD and alert_fired:
            print("[alert-sim] Service recovered. Sending recovery notice.")
            await recovery_notice()
            alert_fired = False
            alert_fired_at = None

        await asyncio.sleep(POLL_INTERVAL)


@app.on_event("startup")
async def startup():
    asyncio.create_task(monitor_loop())


# ── REST API for manual triggering ────────────────────────────────────────

@app.get("/status")
async def status():
    return {
        "alert_active": alert_fired,
        "alert_fired_at": alert_fired_at.isoformat() if alert_fired_at else None,
        "recent_error_rates": error_rate_history[-5:],
        "threshold": THRESHOLD,
        "poll_interval_seconds": POLL_INTERVAL,
    }


@app.post("/trigger")
async def trigger_alert(error_rate: float = 0.95, version: str = "v2.14.0"):
    """Manually fire an alert (for testing/demo purposes)."""
    global alert_fired
    fired = await fire_switch_alert(error_rate, version)
    alert_fired = fired
    return {"fired": fired, "error_rate": error_rate, "version": version}


@app.post("/resolve")
async def resolve_alert():
    """Manually send a recovery notice."""
    global alert_fired
    await recovery_notice()
    alert_fired = False
    return {"resolved": True}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
