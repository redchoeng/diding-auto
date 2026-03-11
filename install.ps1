# ============================================================
#  QESG Installer — 쌩 컴퓨터에서도 딸깍 한번으로 완전 자동 설치
# ============================================================
#
#  사용법: install.bat 더블클릭 (또는 우클릭 → 관리자 권한으로 실행)
# ============================================================

$ErrorActionPreference = "Continue"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "  ================================" -ForegroundColor Cyan
Write-Host "    QESG Installer" -ForegroundColor Cyan
Write-Host "    AI 업무 자동화 비서" -ForegroundColor Cyan
Write-Host "  ================================" -ForegroundColor Cyan
Write-Host ""

# ── Helper: Refresh PATH ─────────────────────────────────────
function Refresh-Path {
    $machinePath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machinePath;$userPath"
}

# ── Helper: Check if winget is available ─────────────────────
function Test-Winget {
    try {
        $null = Get-Command winget -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

# ── 1. Prerequisites — Auto-Install if Missing ──────────────

Write-Host "[1/5] 사전 요구사항 확인 및 설치 중..." -ForegroundColor Yellow

$hasWinget = Test-Winget

# --- Node.js ---
$needNode = $false
if (!(Get-Command node -ErrorAction SilentlyContinue)) {
    $needNode = $true
    Write-Host "  [X] Node.js 미설치 — 자동 설치 시도..." -ForegroundColor Yellow

    if ($hasWinget) {
        Write-Host "      winget으로 Node.js LTS 설치 중..." -ForegroundColor Gray
        winget install OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements --silent 2>&1 | Out-Null
        Refresh-Path
        # Also add default Node.js path
        $nodePaths = @(
            "${env:ProgramFiles}\nodejs",
            "${env:ProgramFiles(x86)}\nodejs"
        )
        foreach ($p in $nodePaths) {
            if ((Test-Path $p) -and ($env:Path -notlike "*$p*")) {
                $env:Path = "$p;$env:Path"
            }
        }
    }

    # Verify
    if (Get-Command node -ErrorAction SilentlyContinue) {
        Write-Host "  [OK] Node.js $(node --version) 설치 완료!" -ForegroundColor Green
        $needNode = $false
    } else {
        Write-Host "  [!] Node.js 자동 설치 실패" -ForegroundColor Red
    }
} else {
    Write-Host "  [OK] Node.js $(node --version)" -ForegroundColor Green
}

# --- Python ---
$needPython = $false
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    $needPython = $true
    Write-Host "  [X] Python 미설치 — 자동 설치 시도..." -ForegroundColor Yellow

    if ($hasWinget) {
        Write-Host "      winget으로 Python 3.12 설치 중..." -ForegroundColor Gray
        winget install Python.Python.3.12 --accept-source-agreements --accept-package-agreements --silent 2>&1 | Out-Null
        Refresh-Path
        # Also add default Python paths
        $pyPaths = @(
            "$env:LOCALAPPDATA\Programs\Python\Python312",
            "$env:LOCALAPPDATA\Programs\Python\Python312\Scripts",
            "${env:ProgramFiles}\Python312",
            "${env:ProgramFiles}\Python312\Scripts"
        )
        foreach ($p in $pyPaths) {
            if ((Test-Path $p) -and ($env:Path -notlike "*$p*")) {
                $env:Path = "$p;$env:Path"
            }
        }
    }

    # Verify
    if (Get-Command python -ErrorAction SilentlyContinue) {
        Write-Host "  [OK] Python $(python --version 2>&1) 설치 완료!" -ForegroundColor Green
        $needPython = $false
    } else {
        Write-Host "  [!] Python 자동 설치 실패" -ForegroundColor Red
    }
} else {
    Write-Host "  [OK] Python $(python --version 2>&1)" -ForegroundColor Green
}

# If still missing, fall back to manual instructions
if ($needNode -or $needPython) {
    Write-Host ""
    Write-Host "  ── 자동 설치 실패: 수동 설치가 필요합니다 ──" -ForegroundColor Red
    Write-Host ""
    if ($needNode) {
        Write-Host "  1. Node.js: https://nodejs.org 에서 LTS 다운로드 → 설치" -ForegroundColor Yellow
        Start-Process "https://nodejs.org"
    }
    if ($needPython) {
        Write-Host "  2. Python: https://www.python.org/downloads/ 에서 다운로드 → 설치" -ForegroundColor Yellow
        Write-Host "     (중요!) 설치 화면 하단 'Add Python to PATH' 반드시 체크!" -ForegroundColor White
        Start-Process "https://www.python.org/downloads/"
    }
    Write-Host ""
    Write-Host "  설치 완료 후 install.bat를 다시 실행하세요." -ForegroundColor Cyan
    Read-Host "  엔터를 누르면 종료합니다"
    exit 1
}

# ── 2. Install Dependencies ─────────────────────────────────

Write-Host ""
Write-Host "[2/5] 패키지 설치 중..." -ForegroundColor Yellow

# Ensure pip is up to date
Write-Host "  pip 업데이트 중..." -ForegroundColor Gray
$null = cmd /c "python -m pip install --upgrade pip 2>&1"

# gws CLI
Write-Host "  gws CLI 설치 중..." -ForegroundColor Gray
$null = cmd /c "npm install -g @googleworkspace/cli 2>&1"
$npmGlobal = Join-Path $env:APPDATA "npm"
if ($env:Path -notlike "*$npmGlobal*") {
    $env:Path = "$npmGlobal;$env:Path"
}
if ((Get-Command gws -ErrorAction SilentlyContinue) -or (Test-Path (Join-Path $npmGlobal "gws.cmd"))) {
    Write-Host "  [OK] gws CLI" -ForegroundColor Green
} else {
    Write-Host "  [!] gws 설치 실패. 'npm install -g @googleworkspace/cli' 수동 실행 필요" -ForegroundColor Red
}

# qesg + flet + llm dependencies
Write-Host "  qesg + AI 패키지 설치 중 (1-2분 소요)..." -ForegroundColor Gray
$null = cmd /c "pip install -e `"$scriptDir[llm]`" 2>&1"
if (Get-Command qesg -ErrorAction SilentlyContinue) {
    Write-Host "  [OK] qesg CLI" -ForegroundColor Green
} else {
    Write-Host "  [OK] qesg 설치됨 (PATH 재시작 후 활성화)" -ForegroundColor Green
}

# ── 3. Create Launcher Script ───────────────────────────────

Write-Host ""
Write-Host "[3/5] 런처 생성 중..." -ForegroundColor Yellow

$launcherPath = Join-Path $scriptDir "QESG.bat"
$launcherContent = @"
@echo off
cd /d "$scriptDir"
python -m qesg.app.main
"@
Set-Content -Path $launcherPath -Value $launcherContent -Encoding ASCII
Write-Host "  [OK] QESG.bat 생성" -ForegroundColor Green

# ── 4. Create Desktop Shortcut ──────────────────────────────

Write-Host ""
Write-Host "[4/5] 바탕화면 바로가기 생성 중..." -ForegroundColor Yellow

$desktopPath = [System.Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "QESG.lnk"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = "pythonw.exe"
$shortcut.Arguments = "-m qesg.app.main"
$shortcut.WorkingDirectory = $scriptDir
$shortcut.Description = "QESG - AI 업무 자동화 비서"
$shortcut.WindowStyle = 7  # Minimized (hide console)

# Set icon
$icoPath = Join-Path $scriptDir "qesg\app\ding.ico"
if (Test-Path $icoPath) {
    $shortcut.IconLocation = "$icoPath,0"
} else {
    $pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
    if ($pythonPath) {
        $shortcut.IconLocation = "$pythonPath,0"
    }
}

$shortcut.Save()
Write-Host "  [OK] 바탕화면에 'QESG' 바로가기 생성" -ForegroundColor Green

# ── 5. Done ─────────────────────────────────────────────────

Write-Host ""
Write-Host "  ================================" -ForegroundColor Green
Write-Host "    설치 완료!" -ForegroundColor Green
Write-Host "  ================================" -ForegroundColor Green
Write-Host ""
Write-Host "  바탕화면의 'QESG' 아이콘을 더블클릭하면 앱이 실행됩니다." -ForegroundColor Cyan
Write-Host ""
Write-Host "  첫 실행 시 설정 탭에서:" -ForegroundColor Yellow
Write-Host "    1. Google OAuth 키 입력 → 구글 로그인" -ForegroundColor White
Write-Host "    2. LLM API 키 입력 (Gemini 무료)" -ForegroundColor White
Write-Host ""

# Ask if user wants to launch now
$launch = Read-Host "  지금 QESG를 실행할까요? (Y/n)"
if ($launch -ne "n" -and $launch -ne "N") {
    Write-Host "  앱을 실행합니다..." -ForegroundColor Cyan
    Start-Process "pythonw.exe" -ArgumentList "-m qesg.app.main" -WorkingDirectory $scriptDir
}
