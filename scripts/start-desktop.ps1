$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Test-Path -LiteralPath "node_modules")) {
  pnpm install
}

if (-not (Test-Path -LiteralPath "dist\client\index.html")) {
  pnpm build
}

pnpm desktop

