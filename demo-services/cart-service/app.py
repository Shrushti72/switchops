"""
SwitchOps — cart-service
────────────────────────
A simple Flask app simulating a shopping cart API.
Set FAIL_RATE=1.0 to make it return 500s (simulates an incident).
Set FAIL_RATE=0.0 to restore it (simulates a rollback).
"""

import os
import random
import time
from datetime import datetime, timezone

from flask import Flask, jsonify

app = Flask(__name__)

FAIL_RATE = float(os.getenv("FAIL_RATE", "0.0"))
VERSION = os.getenv("SERVICE_VERSION", "v2.14.0")
PORT = int(os.getenv("PORT", "8001"))

# Track request stats
stats = {"total": 0, "errors": 0, "start_time": time.time()}


def get_error_rate() -> float:
    if stats["total"] == 0:
        return 0.0
    return stats["errors"] / stats["total"]


@app.route("/health")
def health():
    fail_rate = float(os.getenv("FAIL_RATE", "0.0"))
    return jsonify({
        "status": "degraded" if fail_rate > 0.5 else "healthy",
        "version": VERSION,
        "fail_rate": fail_rate,
    })


@app.route("/cart", methods=["GET", "POST"])
def cart():
    """Main cart endpoint — randomly fails based on FAIL_RATE."""
    fail_rate = float(os.getenv("FAIL_RATE", "0.0"))
    stats["total"] += 1

    if random.random() < fail_rate:
        stats["errors"] += 1
        # Simulate the bug introduced in v2.14.0
        return jsonify({
            "error": "NullPointerException in checkout handler",
            "trace": "checkout.py:142 → cart_total() → None.items()",
            "version": VERSION,
        }), 500

    return jsonify({
        "cart_id": f"cart_{random.randint(1000, 9999)}",
        "items": [{"sku": "SKU-001", "qty": 2, "price": 29.99}],
        "total": 59.98,
        "version": VERSION,
    })


@app.route("/checkout", methods=["POST"])
def checkout():
    """Checkout endpoint — always fails in v2.14.0 simulation."""
    fail_rate = float(os.getenv("FAIL_RATE", "0.0"))
    stats["total"] += 1

    if fail_rate > 0.0:
        stats["errors"] += 1
        return jsonify({
            "error": "Internal Server Error",
            "message": "Checkout failed: null reference in payment handler",
            "version": VERSION,
        }), 500

    return jsonify({"status": "success", "order_id": f"ORD-{random.randint(10000, 99999)}"})


@app.route("/metrics")
def metrics():
    """Metrics endpoint — the alert simulator polls this."""
    uptime = time.time() - stats["start_time"]
    return jsonify({
        "service": "cart-service",
        "version": VERSION,
        "uptime_seconds": round(uptime),
        "total_requests": stats["total"],
        "error_count": stats["errors"],
        "error_rate": round(get_error_rate(), 4),
        "fail_rate_config": float(os.getenv("FAIL_RATE", "0.0")),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
