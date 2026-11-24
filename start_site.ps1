$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$venvPy = Join-Path $root ".venv\Scripts\python.exe"
$backendDir = Join-Path $root "backend"
$frontendDir = Join-Path $root "frontend"
$siteUrl = "http://127.0.0.1:5173"
$healthUrl = "http://127.0.0.1:8000/api/health"
$ws = New-Object -ComObject WScript.Shell

function Test-Port([int]$port) {
    try {
        $conn = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction Stop
        return [bool]$conn
    } catch {
        $found = netstat -ano | Select-String ":$port\s+.*LISTENING"
        return [bool]$found
    }
}

Write-Host "============================================"
Write-Host " Zhixueyun - one-click start"
Write-Host "============================================"
Write-Host ""

Write-Host "[1/3] Checking backend (8000)..."
if (-not (Test-Port 8000)) {
    if (-not (Test-Path $venvPy)) {
        Write-Host "[ERROR] Python venv not found: $venvPy"
        Write-Host "Create it with: python -m venv .venv"
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "Starting backend..."
    $backendCmd = 'cmd /k cd /d "' + $backendDir + '" && "' + $venvPy + '" -m uvicorn app.main:app --host 127.0.0.1 --port 8000'
    $ws.Run($backendCmd, 1, $false) | Out-Null
} else {
    Write-Host "Backend is already running."
}

Write-Host "[2/3] Checking frontend (5173)..."
if (-not (Test-Port 5173)) {
    if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
        Write-Host "[ERROR] frontend\node_modules not found."
        Write-Host "Run: cd frontend; npm install --registry=https://registry.npmmirror.com"
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "Starting frontend..."
    $frontendCmd = 'cmd /k cd /d "' + $frontendDir + '" && npm run dev -- --host 127.0.0.1 --port 5173 --strictPort'
    $ws.Run($frontendCmd, 1, $false) | Out-Null
} else {
    Write-Host "Frontend is already running."
}

Write-Host "[3/3] Waiting for services..."
$ok = $false
for ($i = 0; $i -lt 40; $i++) {
    try {
        $h = Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 $healthUrl
        $f = Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 "$siteUrl/"
        if ($h.StatusCode -eq 200 -and $f.StatusCode -eq 200) {
            $ok = $true
            break
        }
    } catch {
    }
    Start-Sleep -Milliseconds 500
}

if (-not $ok) {
    Write-Host "[WARN] Services did not become ready within 20 seconds."
    Write-Host "Check the backend and frontend windows for errors."
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Opening browser..."
Start-Process $siteUrl
Write-Host ""
Write-Host "Website : $siteUrl"
Write-Host "API docs: http://127.0.0.1:8000/docs"
Write-Host "Accounts: student / admin / teacher_wang / teacher_li"
Write-Host "Password: 123456"
Write-Host ""
Write-Host "Keep the backend and frontend windows open while using the site."
Start-Sleep -Seconds 3