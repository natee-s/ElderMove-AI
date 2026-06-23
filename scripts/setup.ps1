param(
    [switch]$RunApp
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPath = Join-Path $ProjectRoot ".venv"
$Python = Get-Command python, py -ErrorAction SilentlyContinue | Select-Object -First 1

if (-not $Python) {
    throw "Python was not found. Install Python 3.11 or 3.12 from python.org, then run this script again."
}

if (-not (Test-Path $VenvPath)) {
    $PythonArguments = @()
    if ($Python.Name -eq "py") {
        $PythonArguments += "-3"
    }
    $PythonArguments += @("-m", "venv", $VenvPath)
    & $Python.Source @PythonArguments
}

$VenvPython = Join-Path $VenvPath "Scripts\\python.exe"
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -r (Join-Path $ProjectRoot "requirements.txt")

Write-Host "Setup complete. VSCode interpreter: $VenvPython"
if ($RunApp) {
    & $VenvPython -m streamlit run (Join-Path $ProjectRoot "app\\streamlit_app.py")
}
