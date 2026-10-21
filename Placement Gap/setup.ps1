$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = 'C:\Users\VINUTEJ\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$pnpm = 'C:\Users\VINUTEJ\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback\pnpm.cmd'
if (-not (Test-Path -LiteralPath $python)) { $python = (Get-Command py -ErrorAction Stop).Source; & $python -3.12 -m venv (Join-Path $root '.venv') } else { & $python -m venv (Join-Path $root '.venv') }
& (Join-Path $root '.venv\Scripts\python.exe') -m pip install --upgrade pip
& (Join-Path $root '.venv\Scripts\python.exe') -m pip install -e (Join-Path $root '.[dev]')
& $pnpm --dir (Join-Path $root 'web') install
Write-Output 'Dependencies installed. Start the website with .\start.ps1.'
