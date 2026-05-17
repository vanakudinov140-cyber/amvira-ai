# Публичный HTTPS URL для demo (Cloudflare Quick Tunnel → localhost:8080)
# Требует исходящий доступ к api.trycloudflare.com и Cloudflare edge.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Cloudflared = Join-Path $Root "scripts\cloudflared.exe"
$UrlFile = Join-Path $Root "demo-public-url.txt"
$LogFile = Join-Path $env:TEMP "retention-demo-cloudflared.log"

if (-not (Test-Path $Cloudflared)) {
    Write-Host "Скачиваю cloudflared..."
    Invoke-WebRequest `
        -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" `
        -OutFile $Cloudflared
}

# Остановить docker cloudflared (если запущен)
Set-Location $Root
$prevEap = $ErrorActionPreference
$ErrorActionPreference = "SilentlyContinue"
docker compose -f docker-compose.demo.yml --profile public stop cloudflared-quick *>$null
docker compose -f docker-compose.demo.yml --profile public stop cloudflared *>$null
$ErrorActionPreference = $prevEap

# Убить старые процессы quick tunnel
Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host "Запуск Cloudflare Quick Tunnel → http://127.0.0.1:8080"
Write-Host "Лог: $LogFile"

Remove-Item -Path $LogFile -Force -ErrorAction SilentlyContinue

$proc = Start-Process -FilePath $Cloudflared `
    -ArgumentList @("tunnel", "--no-autoupdate", "--protocol", "http2", "--retries", "10", "--url", "http://127.0.0.1:8080", "--logfile", $LogFile) `
    -PassThru `
    -WindowStyle Hidden

$deadline = (Get-Date).AddMinutes(2)
$url = $null
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 2
    if (Test-Path $LogFile) {
        $m = Select-String -Path $LogFile -Pattern "https://[a-z0-9-]+\.trycloudflare\.com" | Select-Object -Last 1
        if ($m) {
            $url = $m.Matches[0].Value
            break
        }
        if (Select-String -Path $LogFile -Pattern "failed to request quick Tunnel") {
            break
        }
    }
}

if ($url) {
    $url | Set-Content -Path $UrlFile -Encoding utf8
    Write-Host ""
    Write-Host "Публичная demo-ссылка:"
    Write-Host $url
    Write-Host ""
    Write-Host "Сохранено в: $UrlFile"
    Write-Host "PID cloudflared: $($proc.Id) (не закрывайте окно / не останавливайте процесс)"
} else {
    Write-Host ""
    Write-Host "Не удалось получить URL. Проверьте $LogFile"
    Write-Host "Возможные причины: блокировка Cloudflare, VPN, корпоративный firewall."
    Write-Host "Альтернатива: named tunnel с токеном (см. .env.demo.example)"
    exit 1
}
