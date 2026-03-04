@echo off
REM ============================================
REM Qwen3.5 - STANDARD PROFILE
REM
REM NOTE: "standard" no longer means multi-server.
REM 35B alone fills 15.5GB — no room for others.
REM This script starts the RECOMMENDED daily driver:
REM   Coding tasks  -> 35B-A3B (port 8002)
REM   Vision tasks  -> 9B      (port 8003)
REM   Quality tasks -> 27B     (port 8004)
REM
REM Use start_servers_speed.bat [coding|vision|quality]
REM to select which one to run.
REM ============================================

echo.
echo ============================================
echo  RTX 5080 16GB — ONE SERVER AT A TIME
echo ============================================
echo.
echo  These models cannot run simultaneously:
echo.
echo  [1] CODING  - 35B-A3B Q3_K_S  port 8002  ~124 t/s  152K ctx
echo  [2] VISION  - 9B Q4_K_XL      port 8003  ~97  t/s  256K ctx
echo  [3] QUALITY - 27B Q3_K_S      port 8004  ~36  t/s  64K  ctx
echo.
echo  Usage: start_servers_speed.bat coding
echo         start_servers_speed.bat vision
echo         start_servers_speed.bat quality
echo.
echo  Starting default (coding) in 5 seconds...
echo  Press Ctrl+C to cancel.
echo.
timeout /t 5 /nobreak >nul

call start_servers_speed.bat coding
