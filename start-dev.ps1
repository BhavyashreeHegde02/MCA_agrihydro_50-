$ErrorActionPreference = "Stop"

$repoRoot = $PSScriptRoot
$backendUrl = "http://127.0.0.1:8000"
$frontendUrl = "http://127.0.0.1:3000"
$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
$frontendDir = Join-Path $repoRoot "frontend"

function Get-ListeningPids([int]$Port) {
    $listeners = @(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue)
    return @($listeners | Select-Object -ExpandProperty OwningProcess -Unique)
}

function Test-BackendHealth {
    try {
        $health = Invoke-RestMethod -Uri "$backendUrl/health" -TimeoutSec 3
        return $health.status -eq "ok"
    } catch {
        return $false
    }
}

function Test-Frontend {
    try {
        $response = Invoke-WebRequest -Uri $frontendUrl -TimeoutSec 5 -UseBasicParsing
        return $response.StatusCode -eq 200 -and $response.Content -match "JALACHAKRA"
    } catch {
        return $false
    }
}

function Wait-ForService([scriptblock]$Probe, [string]$Name, [int]$TimeoutSeconds) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (& $Probe) {
            return
        }
        Start-Sleep -Seconds 2
    }
    throw "$Name did not become ready within $TimeoutSeconds seconds. Check its terminal window for the startup error."
}

if (-not (Test-Path -LiteralPath $python)) {
    throw "Python environment not found at $python. Set it up once with: py -m venv .venv; .\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt"
}

if (-not (Test-Path -LiteralPath (Join-Path $frontendDir "node_modules"))) {
    throw "Frontend dependencies are missing. Set them up once with: Set-Location frontend; npm install"
}

$npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
if (-not $npm) {
    throw "npm.cmd was not found. Install Node.js LTS, reopen PowerShell, and run this script again."
}

if (Test-BackendHealth) {
    Write-Host "Backend is already healthy at $backendUrl"
} else {
    $backendPids = @(Get-ListeningPids -Port 8000)
    if ($backendPids.Count -gt 0) {
        throw "Port 8000 is already occupied by PID(s) $($backendPids -join ', '), but $backendUrl/health is not healthy. Stop the conflicting process or inspect it, then rerun this script."
    }

    Write-Host "Starting backend; waiting for $backendUrl/health ..."
    Start-Process -FilePath $python `
        -ArgumentList @("-m", "uvicorn", "app.main:app", "--app-dir", "backend", "--host", "127.0.0.1", "--port", "8000", "--reload") `
        -WorkingDirectory $repoRoot
    Wait-ForService -Probe { Test-BackendHealth } -Name "Backend" -TimeoutSeconds 90
    Write-Host "Backend is healthy."
}

if (Test-Frontend) {
    Write-Host "Frontend is already responding at $frontendUrl"
} else {
    $frontendPids = @(Get-ListeningPids -Port 3000)
    if ($frontendPids.Count -gt 0) {
        throw "Port 3000 is already occupied by PID(s) $($frontendPids -join ', '), but the Jalachakra frontend is not responding there. Stop the conflicting process or inspect it, then rerun this script."
    }

    Write-Host "Starting frontend ..."
    Start-Process -FilePath $npm.Source `
        -ArgumentList @("run", "dev", "--", "--hostname", "127.0.0.1", "--port", "3000") `
        -WorkingDirectory $frontendDir
    Wait-ForService -Probe { Test-Frontend } -Name "Frontend" -TimeoutSeconds 120
}

Write-Host ""
Write-Host "Jalachakra is ready: $frontendUrl"
Write-Host "Backend health: $backendUrl/health"
Write-Host "Close the backend and frontend terminal windows, or press Ctrl+C in each, to stop the servers."
