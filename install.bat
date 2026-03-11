@echo off
chcp 65001 >nul 2>&1
echo.
echo  QESG 설치를 시작합니다...
echo.

:: 관리자 권한 확인
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo  관리자 권한으로 다시 실행합니다...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: 스크립트 폴더로 이동
cd /d "%~dp0"

:: PowerShell 실행
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0install.ps1"

echo.
pause
