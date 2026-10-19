# Windows alternative to `make check` — run from repo root in PowerShell
# To use `make` instead: winget install GnuWin32.Make

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "==> secrets scan"
$found = Get-ChildItem -Recurse -Include "*.py" src, tests, scripts |
    Select-String -Pattern "sk-ant-api|ANTHROPIC_API_KEY\s*=\s*['""]|OPENAI_API_KEY\s*=\s*['""]"
if ($found) {
    Write-Error "Possible API key in source: $found"
    exit 1
}
Write-Host "    ok"

Write-Host "==> lint (ruff)"
uv run ruff check src/ tests/ scripts/

Write-Host "==> types (pyright)"
uv run pyright src/

Write-Host "==> tests (offline)"
uv run pytest tests/ --co -q

Write-Host "`nAll checks passed."
