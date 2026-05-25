param(
    [string]$MinPythonVersion = "3.10",
    [string]$VenvDir = ".venv",
    [switch]$SkipPythonInstall,
    [switch]$ForceRecreateVenv,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "[setup] $Message"
}

function Get-PythonInfo {
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $ver = & python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))" 2>$null
        if ($LASTEXITCODE -eq 0 -and $ver) {
            return [pscustomobject]@{ Cmd = "python"; Version = $ver }
        }
    }

    if (Get-Command py -ErrorAction SilentlyContinue) {
        $ver = & py -3 -c "import sys; print('.'.join(map(str, sys.version_info[:3])))" 2>$null
        if ($LASTEXITCODE -eq 0 -and $ver) {
            return [pscustomobject]@{ Cmd = "py -3"; Version = $ver }
        }
    }

    return $null
}

function Test-MinVersion {
    param(
        [string]$Current,
        [string]$Minimum
    )
    return ([Version]$Current -ge [Version]$Minimum)
}

function Install-PythonOnWindows {
    Write-Step "Python not found or version too low. Trying to install with winget..."

    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw "winget is not available. Install Python manually from https://www.python.org/downloads/ and re-run this script."
    }

    $pkg = "Python.Python.3.13"
    $cmd = "winget install --id $pkg --exact --silent --accept-package-agreements --accept-source-agreements"

    if ($DryRun) {
        Write-Step "[dry-run] $cmd"
        return
    }

    Invoke-Expression $cmd
}

function Invoke-Step {
    param([string]$Command)

    if ($DryRun) {
        Write-Step "[dry-run] $Command"
        return
    }

    Invoke-Expression $Command
}

Write-Step "Working directory: $PSScriptRoot"
Set-Location $PSScriptRoot

$pythonInfo = Get-PythonInfo

if ($null -eq $pythonInfo -or -not (Test-MinVersion -Current $pythonInfo.Version -Minimum $MinPythonVersion)) {
    if ($SkipPythonInstall) {
        throw "Python >= $MinPythonVersion is required, but was not found. Remove -SkipPythonInstall or install Python manually."
    }

    Install-PythonOnWindows
    $pythonInfo = Get-PythonInfo

    if ($null -eq $pythonInfo -or -not (Test-MinVersion -Current $pythonInfo.Version -Minimum $MinPythonVersion)) {
        throw "Python installation did not complete as expected. Please open a new terminal and re-run setup.ps1."
    }
}

Write-Step "Using Python: $($pythonInfo.Cmd) (version $($pythonInfo.Version))"

$venvPath = Join-Path $PSScriptRoot $VenvDir

if ((Test-Path $venvPath) -and $ForceRecreateVenv) {
    Write-Step "Removing old virtual environment: $venvPath"
    if (-not $DryRun) {
        Remove-Item -Path $venvPath -Recurse -Force
    }
}

if (-not (Test-Path $venvPath)) {
    Write-Step "Creating virtual environment at $venvPath"
    if ($pythonInfo.Cmd -eq "python") {
        Invoke-Step "python -m venv `"$venvPath`""
    }
    else {
        Invoke-Step "py -3 -m venv `"$venvPath`""
    }
}
else {
    Write-Step "Virtual environment already exists: $venvPath"
}

$venvPython = Join-Path $venvPath "Scripts\python.exe"
if ((-not $DryRun) -and (-not (Test-Path $venvPython))) {
    throw "Virtual environment python not found: $venvPython"
}

Write-Step "Upgrading pip/setuptools/wheel"
Invoke-Step "`"$venvPython`" -m pip install --upgrade pip setuptools wheel"

$requirementsFile = Join-Path $PSScriptRoot "requirements.txt"
if (-not (Test-Path $requirementsFile)) {
    throw "requirements.txt not found in project root: $requirementsFile"
}

Write-Step "Installing dependencies from requirements.txt"
Invoke-Step "`"$venvPython`" -m pip install -r `"$requirementsFile`""

Write-Step "Setup complete."
Write-Step "Activate venv with: .\\$VenvDir\\Scripts\\Activate.ps1"
Write-Step "Run tests with: pytest '@tests_to_run.txt'"
