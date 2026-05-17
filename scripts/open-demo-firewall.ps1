# Требует PowerShell от администратора
$rules = @(
    @{ Name = "Retention Demo Dashboard 8080"; Port = 8080 },
    @{ Name = "Retention Demo API 8000"; Port = 8000 }
)
foreach ($r in $rules) {
    $existing = Get-NetFirewallRule -DisplayName $r.Name -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "Правило уже есть: $($r.Name)"
        continue
    }
    New-NetFirewallRule -DisplayName $r.Name -Direction Inbound -Action Allow -Protocol TCP -LocalPort $r.Port | Out-Null
    Write-Host "Открыт TCP $($r.Port): $($r.Name)"
}
