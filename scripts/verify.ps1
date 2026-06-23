$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot ".venv\\Scripts\\python.exe"

if (-not (Test-Path $VenvPython)) {
    throw "Virtual environment not found. Run scripts/setup.ps1 first."
}

Push-Location $ProjectRoot
try {
    & $VenvPython -m compileall app src tests
    & $VenvPython -m pytest -q
}
finally {
    Pop-Location
}
