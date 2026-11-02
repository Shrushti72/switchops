#!/usr/bin/env bash
# break-cart.sh — Simulates the v2.14.0 incident (100% error rate)
set -e

echo "🔥 Breaking cart-service (simulating v2.14.0 bug)..."
docker exec switchops-cart bash -c "export FAIL_RATE=1.0" 2>/dev/null || \
  docker compose up -d --no-deps -e FAIL_RATE=1.0 -e SERVICE_VERSION=v2.14.0 cart-service

# Alternatively, update the running container environment:
docker exec switchops-cart sh -c \
  "python -c \"import os; open('/tmp/fail_rate', 'w').write('1.0')\"" 2>/dev/null || true

# Restart with the broken env via compose
docker compose stop cart-service
FAIL_RATE=1.0 SERVICE_VERSION=v2.14.0 docker compose up -d cart-service

echo "✅ cart-service is now returning 500s"
echo "   The alert simulator will detect this in ~10s and fire the alert to Switch."
echo ""
echo "   Watch your Discord channel for @switchops-radar to respond!"
echo ""
echo "   To recover: ./scripts/fix-cart.sh"
