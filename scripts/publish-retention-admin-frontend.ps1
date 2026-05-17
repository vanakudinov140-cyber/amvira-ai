# Публикует retention-admin-frontend в отдельный GitHub-репозиторий (корень = SPA).
# Использование:
#   .\scripts\publish-retention-admin-frontend.ps1 -RemoteUrl "https://github.com/USER/retention-admin-frontend.git"

param(
    [Parameter(Mandatory = $true)]
    [string]$RemoteUrl
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$Src = Join-Path $Root "retention-admin-frontend"
if (-not (Test-Path (Join-Path $Src "Dockerfile"))) {
    throw "Not found: $Src\Dockerfile"
}
$Tmp = Join-Path $env:TEMP "retention-admin-frontend-publish"

if (Test-Path $Tmp) { Remove-Item $Tmp -Recurse -Force }
New-Item -ItemType Directory -Path $Tmp | Out-Null
robocopy $Src $Tmp /E /XD node_modules dist .git .vercel /NFL /NDL /NJH /NJS | Out-Null

Push-Location $Tmp
try {
    git init
    git add .
    git commit -m "chore: publish standalone retention admin frontend"
    git branch -M main
    git remote add origin $RemoteUrl
    git push -u origin main --force
    Write-Host "Published to $RemoteUrl"
}
finally {
    Pop-Location
}
