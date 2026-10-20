# Windows alternative to `make check` — run from repo root in PowerShell
# To use `make` instead: winget install GnuWin32.Make

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "==> secrets scan"
$dirs = "src", "tests", "scripts", "cassettes", "results", "runs" | Where-Object { Test-Path $_ }
$found = Get-ChildItem -Recurse -File $dirs |
    Select-String -Pattern "sk-ant-api|sk-[a-zA-Z0-9]{20}|ANTHROPIC_API_KEY\s*=\s*['""]|OPENAI_API_KEY\s*=\s*['""]"
if ($found) {
    Write-Error "Possible API key in source: $found"
    exit 1
}
Write-Host "    ok"

Write-Host "==> lint (ruff)"
uv run ruff check src/ tests/ scripts/
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> types (pyright)"
uv run pyright src/
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> tests (offline)"
uv run pytest tests/ -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> claims match artifacts"
uv run python scripts/check_claims.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`nAll checks passed."
