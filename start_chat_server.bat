@echo off
REM ============================================================================
REM  Qwen3.5 — Model Switcher
REM  RTX 5080 16GB — ONE SERVER AT A TIME
REM
REM  USAGE:
REM    start_chat_server.bat           <- 35B (default, best quality)
REM    start_chat_server.bat 35b       <- 35B MoE  ~100 t/s  14.2GB  64K ctx
REM    start_chat_server.bat 9b        <- 9B       ~97  t/s   5.6GB  64K ctx  (fastest vision)
REM    start_chat_server.bat 27b       <- 27B      ~36  t/s  11.5GB  64K ctx  (highest quality)
REM
REM  Then in another terminal:
REM    python chat.py              <- connects to whichever model is running
REM    python chat.py --port 8003  <- 9B model
REM    python chat.py --port 8004  <- 27B model
REM ============================================================================

set LLAMA_EXE=%~dp0llama.cpp\build-sm120\bin\Release\llama-server.exe
set MODELS=%~dp0models\unsloth-gguf
set LOGDIR=%~dp0logs
set MODEL=%~1
if "%MODEL%"=="" set MODEL=35b

if not exist "%LOGDIR%" mkdir "%LOGDIR%"

REM ── Kill ALL running llama-server instances ──────────────────────────────────
echo.
echo [*] Killing any running llama-server...
taskkill /F /IM llama-server.exe 2>nul
timeout /t 3 /nobreak >nul
echo [*] VRAM freed.
echo.

REM ── Route to model ───────────────────────────────────────────────────────────
if /i "%MODEL%"=="35b"  goto :model_35b
if /i "%MODEL%"=="9b"   goto :model_9b
if /i "%MODEL%"=="27b"  goto :model_27b
echo [!] Unknown model: %MODEL%
echo     Usage: start_chat_server.bat [35b^|9b^|27b]
exit /b 1

REM ============================================================================
:model_35b
echo ============================================
echo  MODEL : Qwen3.5-35B-A3B-Q3_K_S  (MoE)
echo  PORT  : 8002
echo  SPEED : ~100 t/s gen / 741 t/s prompt
echo  VRAM  : ~15.1 GB   CTX: 64K
echo  BEST FOR: coding, reasoning, long tasks
echo  VISION: YES  (auto-resize to 768px)
echo ============================================
echo.
set PORT=8002
set MODELFILE=%MODELS%\Qwen3.5-35B-A3B-Q3_K_S.gguf
set MMPROJFILE=%MODELS%\mmproj-35B-F16.gguf
set CTX=65536
set EXTRA_ARGS=--parallel 1 --reasoning-budget 0
goto :launch

REM ============================================================================
:model_9b
echo ============================================
echo  MODEL : Qwen3.5-9B-UD-Q4_K_XL
echo  PORT  : 8003
echo  SPEED : ~97 t/s gen / 500+ t/s prompt
echo  VRAM  : ~5.6 GB   CTX: 64K
echo  BEST FOR: fast vision, quick answers
echo  VISION: YES  (fastest — 10GB VRAM free)
echo ============================================
echo.
set PORT=8003
set MODELFILE=%MODELS%\Qwen3.5-9B-UD-Q4_K_XL.gguf
set MMPROJFILE=%MODELS%\mmproj-F16.gguf
set CTX=65536
set EXTRA_ARGS=--reasoning-budget 0
goto :launch

REM ============================================================================
:model_27b
echo ============================================
echo  MODEL : Qwen3.5-27B-Q3_K_S  (dense)
echo  PORT  : 8004
echo  SPEED : ~36 t/s gen / 325 t/s prompt
echo  VRAM  : ~11.5 GB  CTX: 64K
echo  BEST FOR: highest quality, nuanced writing
echo  VISION: YES
echo ============================================
echo.
set PORT=8004
set MODELFILE=%MODELS%\Qwen3.5-27B-Q3_K_S.gguf
set MMPROJFILE=%MODELS%\mmproj-27B-F16.gguf
set CTX=65536
set EXTRA_ARGS=
goto :launch

REM ============================================================================
:launch
echo [*] Starting model on port %PORT%...
echo [*] Log: %LOGDIR%\server-%PORT%-err.log
echo.

REM Use wmic to launch fully detached (survives this bat closing)
wmic process call create ^
  "\"%LLAMA_EXE%\" -m \"%MODELFILE%\" --mmproj \"%MMPROJFILE%\" --host 127.0.0.1 --port %PORT% -c %CTX% -ngl 99 --flash-attn on -ctk iq4_nl -ctv iq4_nl %EXTRA_ARGS% --temp 0.6 --top-p 0.95 --top-k 20 --presence-penalty 0.0 >> \"%LOGDIR%\server-%PORT%-err.log\" 2>&1" ^
  >nul 2>&1

echo [*] Model loading... (14GB models take 60-90s, 9B takes ~30s)
echo.
echo     When ready, open a NEW terminal and run:
echo.
if "%PORT%"=="8002" echo       python chat.py
if "%PORT%"=="8003" echo       python chat.py --port 8003
if "%PORT%"=="8004" echo       python chat.py --port 8004
echo.
echo     To check if server is ready:
echo       curl http://127.0.0.1:%PORT%/health
echo.
pause
