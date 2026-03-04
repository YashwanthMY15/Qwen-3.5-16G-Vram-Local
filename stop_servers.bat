@echo off
REM ============================================
REM Stop all Qwen3.5 servers
REM ============================================

echo Stopping all llama-server processes...
taskkill /F /IM llama-server.exe 2>nul

if %errorlevel%==0 (
    echo Servers stopped successfully.
) else (
    echo No servers were running.
)

timeout /t 3
