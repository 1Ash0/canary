# Load .env into THIS PowerShell session only (the CLI reads environment variables, not files).
# Usage from the repo root:  . .\scripts\load-env.ps1
# Empty values and comments are skipped. Nothing is printed except the variable names set.

$path = Join-Path (Split-Path $PSScriptRoot -Parent) ".env"
if (-not (Test-Path $path)) { Write-Host ".env not found: copy .env.example to .env first"; return }

foreach ($line in Get-Content $path) {
    if ($line -match '^\s*#' -or $line -notmatch '=') { continue }
    $name, $value = $line -split '=', 2
    $name = $name.Trim(); $value = $value.Trim().Trim('"').Trim("'")
    if ($name -and $value) {
        Set-Item -Path "Env:$name" -Value $value
        Write-Host "set $name"
    }
}
