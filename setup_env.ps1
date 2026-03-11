# qesg CLI 환경 설정 스크립트 (PowerShell)
# 다른 컴퓨터에서 이 스크립트만 실행하면 됩니다.

Write-Host "=== qesg CLI Setup ===" -ForegroundColor Cyan

# 1. Node.js 확인
if (!(Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "[!] Node.js가 설치되어 있지 않습니다." -ForegroundColor Red
    Write-Host "    https://nodejs.org 에서 설치 후 다시 실행하세요."
    exit 1
}
Write-Host "[OK] Node.js $(node --version)" -ForegroundColor Green

# 2. Python 확인
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[!] Python이 설치되어 있지 않습니다." -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Python $(python --version)" -ForegroundColor Green

# 3. gcloud CLI 확인
if (!(Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "[!] gcloud CLI가 설치되어 있지 않습니다." -ForegroundColor Red
    Write-Host "    https://cloud.google.com/sdk/docs/install 에서 설치 후 다시 실행하세요."
    exit 1
}
Write-Host "[OK] gcloud CLI found" -ForegroundColor Green

# 4. gws CLI 설치
Write-Host "`n[1/4] Installing Google Workspace CLI..." -ForegroundColor Yellow
npm install -g @googleworkspace/cli

# 5. qesg CLI 설치
Write-Host "`n[2/4] Installing qesg CLI..." -ForegroundColor Yellow
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
pip install -e $scriptDir

# 6. GCP 프로젝트 설정
Write-Host "`n[3/4] Setting up GCP project..." -ForegroundColor Yellow
gcloud config set project qesg-cli-project

# 7. .env 파일에서 OAuth 환경변수 로드
$envFile = Join-Path $scriptDir ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^([^#][^=]+)=(.+)$") {
            [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
        }
    }
    Write-Host "[OK] .env loaded" -ForegroundColor Green
} else {
    Write-Host "[!] .env 파일이 없습니다. .env.example을 복사해서 OAuth 정보를 입력하세요." -ForegroundColor Red
    Write-Host "    cp .env.example .env" -ForegroundColor Yellow
    exit 1
}

# 8. gws 인증 (브라우저 열림)
Write-Host "`n[4/4] Authenticating with Google..." -ForegroundColor Yellow
Write-Host "      브라우저가 열리면 구글 계정으로 로그인하세요." -ForegroundColor Cyan
gws auth login

# 9. 확인
Write-Host "`n=== Setup Complete ===" -ForegroundColor Cyan
qesg status

# 10. Claude Code 스킬 설치 안내
Write-Host "`n[TIP] Claude Code 스킬로 등록하려면:" -ForegroundColor Yellow
Write-Host "      qesg.md 파일을 ~/.claude/commands/ 에 복사하세요."
