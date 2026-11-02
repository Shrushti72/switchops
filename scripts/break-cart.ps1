# break-cart.ps1 — Simulates the v2.14.0 incident (100% error rate) on Windows
Write-Host "🔥 Breaking cart-service (simulating v2.14.0 bug)..." -ForegroundColor Red

$env:FAIL_RATE = "1.0"
$env:SERVICE_VERSION = "v2.14.0"

docker compose stop cart-service
docker compose up -d cart-service

Write-Host "✅ cart-service is now returning 500s" -ForegroundColor Green
Write-Host "   The alert simulator will detect this in ~10s and fire the alert to Switch."
Write-Host "   Watch your #incidents channel for @switchops-radar to respond!" -ForegroundColor Yellow
Write-Host "   To recover: .\scripts\fix-cart.ps1"
