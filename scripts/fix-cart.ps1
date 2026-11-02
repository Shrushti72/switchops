# fix-cart.ps1 — Rolls back cart-service to v2.13.2 (0% error rate) on Windows
Write-Host "🔄 Rolling back cart-service to v2.13.2..." -ForegroundColor Cyan

$env:FAIL_RATE = "0.0"
$env:SERVICE_VERSION = "v2.13.2"

docker compose stop cart-service
docker compose up -d cart-service

Write-Host "✅ cart-service is healthy (v2.13.2)" -ForegroundColor Green
Write-Host "   The alert simulator will detect recovery in ~10s and notify the room."
