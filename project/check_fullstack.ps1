param(
    [string]$BackendBase = "http://127.0.0.1:8000",
    [string]$FrontendBase = "http://localhost:5175",
    [string]$Username = "admin",
    [string]$Password = "admin123456"
)

$ErrorActionPreference = "Stop"

function Write-Step($text) {
    Write-Host $text -ForegroundColor Cyan
}

function Write-Ok($text) {
    Write-Host "[PASS] $text" -ForegroundColor Green
}

function Write-Warn($text) {
    Write-Host "[WARN] $text" -ForegroundColor Yellow
}

function Write-Fail($text) {
    Write-Host "[FAIL] $text" -ForegroundColor Red
}

$failed = $false

Write-Step "[0/5] Runserver process check..."
try {
    $runservers = Get-CimInstance Win32_Process |
        Where-Object { $_.Name -match '^python(\.exe)?$' -and $_.CommandLine -match 'manage.py runserver' }
    $count = @($runservers).Count
    if ($count -eq 0) {
        Write-Warn "No Django runserver process detected. Start backend before network checks."
    } elseif ($count -eq 1) {
        Write-Ok "One Django runserver process detected."
    } else {
        $failed = $true
        Write-Fail "Detected $count Django runserver processes. Keep only one backend instance."
        $runservers | Select-Object ProcessId, CommandLine | Format-Table -AutoSize
    }
} catch {
    Write-Warn "Unable to inspect runserver processes: $($_.Exception.Message)"
}

Write-Step "[1/5] Django configuration check..."
try {
    python manage.py check | Out-Null
    Write-Ok "Django system check passed."
} catch {
    $failed = $true
    Write-Fail "Django system check failed: $($_.Exception.Message)"
}

Write-Step "[2/5] Database connection check..."
try {
    $dbCheck = python manage.py shell -c "from django.db import connection; c=connection.cursor(); c.execute('SELECT 1'); print('OK')" 2>&1
    if ($dbCheck -match "OK") {
        Write-Ok "Database connection is available."
    } else {
        $failed = $true
        Write-Fail "Database check returned unexpected output: $dbCheck"
    }
} catch {
    $failed = $true
    Write-Fail "Database connection failed. Check MYSQL_* env and MySQL user/password."
}

$origin = $FrontendBase.TrimEnd("/")
$backendLogin = "$($BackendBase.TrimEnd('/'))/api/auth/login/"

Write-Step "[3/5] Backend CORS preflight check..."
try {
    $headers = @{
        "Origin" = $origin
        "Access-Control-Request-Method" = "POST"
        "Access-Control-Request-Headers" = "content-type,authorization"
    }
    $resp = Invoke-WebRequest -Method Options -Uri $backendLogin -Headers $headers -UseBasicParsing
    $acao = $resp.Headers["Access-Control-Allow-Origin"]
    if ($resp.StatusCode -eq 200 -and ($acao -eq $origin -or $acao -eq "*")) {
        Write-Ok "Preflight passed. ACAO=$acao"
    } else {
        $failed = $true
        Write-Fail "Preflight invalid. Status=$($resp.StatusCode), ACAO=$acao"
        Write-Warn "If ACAO is empty, you are likely hitting an old backend process or mismatched settings."
    }
} catch {
    $failed = $true
    Write-Fail "Preflight request failed: $($_.Exception.Message)"
}

Write-Step "[4/5] Backend login API check..."
try {
    $payload = @{ username = $Username; password = $Password } | ConvertTo-Json
    $loginResp = Invoke-RestMethod -Method Post -Uri $backendLogin -ContentType "application/json" -Body $payload
    if ($loginResp.access -and $loginResp.refresh) {
        Write-Ok "Backend login succeeded."
    } else {
        $failed = $true
        Write-Fail "Backend login response missing tokens."
    }
} catch {
    $failed = $true
    Write-Fail "Backend login failed: $($_.Exception.Message)"
}

Write-Step "[5/5] Frontend proxy check (optional)..."
try {
    $frontendPing = Invoke-WebRequest -Method Get -Uri "$($FrontendBase.TrimEnd('/'))/login" -UseBasicParsing
    if ($frontendPing.StatusCode -ge 200 -and $frontendPing.StatusCode -lt 400) {
        $proxyLogin = "$($FrontendBase.TrimEnd('/'))/api/auth/login/"
        $payload = @{ username = $Username; password = $Password } | ConvertTo-Json
        $proxyResp = Invoke-RestMethod -Method Post -Uri $proxyLogin -ContentType "application/json" -Body $payload
        if ($proxyResp.access -and $proxyResp.refresh) {
            Write-Ok "Frontend -> Vite proxy -> Backend API works."
        } else {
            $failed = $true
            Write-Fail "Frontend proxy login response missing tokens."
        }
    } else {
        Write-Warn "Frontend is not running at $FrontendBase. Proxy check skipped."
    }
} catch {
    Write-Warn "Frontend check skipped: $($_.Exception.Message)"
}

Write-Host ""
if ($failed) {
    Write-Fail "Fullstack check finished with failures."
    exit 1
}

Write-Ok "Fullstack check finished successfully."
exit 0
