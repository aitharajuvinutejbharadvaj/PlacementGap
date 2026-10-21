$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $root '.venv\Scripts\python.exe'
$pnpm = 'C:\Users\VINUTEJ\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback\pnpm.cmd'
if (-not (Test-Path -LiteralPath $python)) { throw 'Run setup.ps1 first to install Python dependencies.' }
if (-not (Test-Path -LiteralPath (Join-Path $root 'web\node_modules'))) { & $pnpm --dir (Join-Path $root 'web') install }
$logs = Join-Path $root 'outputs\logs'
New-Item -ItemType Directory -Force -Path $logs | Out-Null
if (-not (Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue)) {
    Start-Process -FilePath $python -ArgumentList @('-m','uvicorn','api.main:app','--host','127.0.0.1','--port','8000') -WorkingDirectory $root -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logs 'api.log') -RedirectStandardError (Join-Path $logs 'api-error.log')
}
if (-not (Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue)) {
    Start-Process -FilePath $pnpm -ArgumentList @('--dir',(Join-Path $root 'web'),'dev') -WorkingDirectory $root -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logs 'web.log') -RedirectStandardError (Join-Path $logs 'web-error.log')
}
$ready = $false
for ($i = 0; $i -lt 20; $i++) {
    try {
        $health = Invoke-RestMethod 'http://127.0.0.1:8000/health' -TimeoutSec 2
        $site = Invoke-WebRequest 'http://127.0.0.1:5173' -UseBasicParsing -TimeoutSec 2
        if ($health.status -eq 'ok' -and $site.StatusCode -eq 200) { $ready = $true; break }
    } catch { Start-Sleep -Milliseconds 500 }
}
if (-not $ready) { throw 'PlacementGap did not become healthy. Check outputs\logs.' }
Write-Output 'PlacementGap is available at http://localhost:5173 (API: http://localhost:8000).'
