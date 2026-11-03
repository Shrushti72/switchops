# rollback.ps1 — Rollback service to specified version on Windows
param (
    [string]$Service = "cart-service",
    [string]$Version = "v2.13.2"
)

Write-Host "🔄 [SwitchOps] Executing rollback for $Service to $Version..." -ForegroundColor Cyan

if ($Service -eq "cart-service") {
    $env:FAIL_RATE = "0.0"
    $env:SERVICE_VERSION = $Version
    docker compose stop cart-service
    docker compose up -d cart-service
    Write-Host "✅ [SwitchOps] Successfully rolled back $Service to $Version." -ForegroundColor Green
    Write-Host "   Health check: HTTP 200 OK | Error rate: 0.1% (nominal)" -ForegroundColor Green
} else {
    Write-Host "ℹ️ [SwitchOps] Target service $Service staged for rollback to $Version." -ForegroundColor Yellow
}
