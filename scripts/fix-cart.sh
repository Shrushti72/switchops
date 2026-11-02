#!/usr/bin/env bash
# fix-cart.sh — Rolls back cart-service to v2.13.2 (0% error rate)
set -e

echo "🔄 Rolling back cart-service to v2.13.2..."

docker compose stop cart-service
FAIL_RATE=0.0 SERVICE_VERSION=v2.13.2 docker compose up -d cart-service

echo "✅ cart-service is healthy (v2.13.2)"
echo "   The alert simulator will detect recovery in ~10s and notify the room."
