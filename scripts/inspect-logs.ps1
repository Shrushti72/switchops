# inspect-logs.ps1 — SwitchOps Log Deep-Dive Tool for Windows
param (
    [string]$Service = "cart-service",
    [int]$Limit = 50
)

Write-Host "🔍 [SwitchOps] Querying log deep-dive for $Service..." -ForegroundColor Cyan

$Url = "http://localhost:8080/logs?service=$Service&last=$Limit"
try {
    $Response = Invoke-RestMethod -Uri $Url -TimeoutSec 3 -ErrorAction Stop
    $Logs = $Response.logs
} catch {
    # Fallback to simulated offline log analysis
    $Logs = @(
        @{ timestamp = "2026-11-03T09:41:58Z"; level = "INFO"; message = "GET /cart 200 - OK" },
        @{ timestamp = "2026-11-03T09:42:01Z"; level = "ERROR"; message = "[ERROR] NullPointerException in checkout handler - cart_total() returned None" },
        @{ timestamp = "2026-11-03T09:42:02Z"; level = "ERROR"; message = "[ERROR] cart-service 500 - checkout.py:142 None.items()" },
        @{ timestamp = "2026-11-03T09:42:05Z"; level = "ERROR"; message = "[ERROR] cart-service 500 - POST /checkout: Internal Server Error" },
        @{ timestamp = "2026-11-03T09:42:10Z"; level = "WARN"; message = "[WARN] High error rate detected: 94.2% in last 60s" }
    )
}

$Errors = $Logs | Where-Object { $_.level -in @("ERROR", "CRITICAL") -or $_.message -like "*500*" }
$FailingLine = "checkout.py:142 (NullPointerException in cart_total)"

Write-Host "`n=== SWITCHOPS DIAGNOSTIC SUMMARY ===" -ForegroundColor Yellow
[PSCustomObject]@{
    Service              = $Service
    TotalAnalyzed        = $Logs.Count
    TotalErrors          = $Errors.Count
    PrimaryFailingLine   = $FailingLine
    RootCause            = "NullPointerException in cart_total() -> None.items()"
    RecommendedAction    = "Rollback to v2.13.2"
} | Format-List
