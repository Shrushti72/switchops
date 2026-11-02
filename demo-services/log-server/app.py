"""
SwitchOps — Log Server
───────────────────────
Serves structured fake logs for the cart-service.
Agents query: GET /logs?service=cart-service&last=50
"""

import os
import random
from datetime import datetime, timezone, timedelta

from flask import Flask, jsonify, request

app = Flask(__name__)

CART_SERVICE_URL = os.getenv("CART_SERVICE_URL", "http://cart-service:8001")


def generate_log_lines(service: str, count: int, inject_errors: bool = False) -> list[dict]:
    """Generate realistic structured log entries."""
    now = datetime.now(timezone.utc)
    lines = []

    templates_ok = [
        f'[INFO] {service} request processed in {{ms}}ms — GET /cart 200',
        f'[INFO] {service} request processed in {{ms}}ms — POST /checkout 200',
        f'[INFO] Cart retrieved for user {{uid}} — items=3 total=$89.97',
        f'[INFO] Session started for user {{uid}}',
        f'[INFO] Cache hit for product SKU-{{sku}}',
        f'[DEBUG] DB query completed in {{ms}}ms — SELECT * FROM carts',
    ]

    templates_err = [
        f'[ERROR] NullPointerException in checkout handler — cart_total() returned None',
        f'[ERROR] {service} 500 — checkout.py:142 None.items()',
        f'[WARN]  Retry attempt 1/3 for user {{uid}} — timeout after 5000ms',
        f'[ERROR] Payment gateway timed out after 30s for order {{oid}}',
        f'[ERROR] {service} 500 — POST /checkout: Internal Server Error',
        f'[WARN]  High error rate detected: {{rate}}% in last 60s',
    ]

    for i in range(count):
        ts = (now - timedelta(seconds=(count - i) * 2)).strftime("%Y-%m-%dT%H:%M:%SZ")
        is_error = inject_errors and random.random() < 0.7

        if is_error:
            tmpl = random.choice(templates_err)
        else:
            tmpl = random.choice(templates_ok)

        line = tmpl.format(
            ms=random.randint(12, 850),
            uid=f"usr_{random.randint(1000, 9999)}",
            sku=random.randint(100, 999),
            oid=f"ORD-{random.randint(10000, 99999)}",
            rate=round(random.uniform(70, 98), 1),
        )

        lines.append({
            "timestamp": ts,
            "level": "ERROR" if "[ERROR]" in line else "WARN" if "[WARN]" in line else "INFO",
            "service": service,
            "message": line,
        })

    # If injecting errors, add the deploy marker near the start of errors
    if inject_errors and count >= 10:
        deploy_ts = (now - timedelta(seconds=count * 2 - 15)).strftime("%Y-%m-%dT%H:%M:%SZ")
        deploy_log = {
            "timestamp": deploy_ts,
            "level": "INFO",
            "service": "deploy-agent",
            "message": "[INFO] deploy-agent — Deployed cart-service v2.14.0 (was v2.13.2) — rollback available",
        }
        insert_at = max(0, count // 2 - 2)
        lines.insert(insert_at, deploy_log)

    return lines


@app.route("/logs")
def get_logs():
    """
    GET /logs?service=cart-service&last=50
    Returns structured log entries. Auto-detects if cart is broken.
    """
    service = request.args.get("service", "cart-service")
    last = min(int(request.args.get("last", "50")), 200)

    # Check if cart is actually failing (to make logs realistic)
    inject_errors = False
    try:
        import httpx
        r = httpx.get(f"{CART_SERVICE_URL}/metrics", timeout=3)
        metrics = r.json()
        inject_errors = metrics.get("fail_rate_config", 0.0) > 0.3
    except Exception:
        pass

    logs = generate_log_lines(service, last, inject_errors=inject_errors)

    # Format as text block (easier for agents to read)
    text_block = "\n".join(
        f"{l['timestamp']} {l['level']:5s} [{l['service']}] {l['message']}"
        for l in logs
    )

    error_count = sum(1 for l in logs if l["level"] == "ERROR")
    warn_count = sum(1 for l in logs if l["level"] == "WARN")

    return jsonify({
        "service": service,
        "count": len(logs),
        "error_count": error_count,
        "warn_count": warn_count,
        "inject_errors": inject_errors,
        "logs": logs,
        "text": text_block,  # Agents can paste this directly into chat
    })


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "log-server"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
