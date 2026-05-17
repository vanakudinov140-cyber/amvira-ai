# Запуск production-like demo (dashboard :8080 + API :8000)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

Write-Host "Building admin-dashboard production bundle..."
Set-Location "$Root\admin-dashboard"
npm run build
Set-Location $Root

Write-Host "Starting docker compose demo stack..."
docker compose -f docker-compose.demo.yml up -d --build

$ip = (
    Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object { $_.IPAddress -like "10.*" -or $_.IPAddress -like "192.168.*" } |
    Select-Object -First 1 -ExpandProperty IPAddress
)
if (-not $ip) { $ip = "127.0.0.1" }

Write-Host ""
Write-Host "Demo dashboard: http://${ip}:8080"
Write-Host "API health:     http://${ip}:8000/health"
Write-Host "API via proxy:  http://${ip}:8080/health"
Write-Host ""
Write-Host "Откройте порты 8080 и 8000 в брандмауэре Windows для доступа с телефона."
