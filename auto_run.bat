@echo off
REM ===========================================================================
REM  GitHub-Trends weekly crawler -- unattended run
REM
REM  ASCII only, no BOM (cmd.exe reads the OEM codepage; non-ASCII comments get
REM  mangled into stray commands). Keep it that way if you edit this file.
REM
REM  Launched by run_hidden.vbs, NOT directly by Task Scheduler. The direct
REM  "cmd.exe /c auto_run.bat" action opened a VISIBLE console window; closing
REM  it killed the crawl with STATUS_CONTROL_C_EXIT. See run_hidden.vbs.
REM
REM  Manual force run (bypasses the "this week is already fresh" gate):
REM      cmd /c "C:\Users\jd\Desktop\github-trends\auto_run.bat" force
REM
REM  State files, all under output\ :
REM      RUNNING.lock      present => a run is in flight, or one was KILLED.
REM                        Every path that ends the script deliberately deletes
REM                        it, so a surviving lock means the process died
REM                        without getting to say goodbye.
REM      CRASH.txt         INTERRUPTED / CRAWL-FAILED / PROXY-DEAD / traceback
REM      auto_log.txt      rotated to auto_log.txt.1 past 512 KB
REM ===========================================================================

setlocal EnableDelayedExpansion
set "ROOT=C:\Users\jd\Desktop\github-trends"
set "LOG=%ROOT%\output\auto_log.txt"
set "LOCK=%ROOT%\output\RUNNING.lock"
set "CRASH=%ROOT%\output\CRASH.txt"
cd /d "%ROOT%"

set "FORCE=0"
if /i "%~1"=="force" set "FORCE=1"
set "ATTEMPT=0"
set "MAX_ATTEMPTS=3"
set "PREV_INTERRUPTED=0"
set "LOCKAGE="

REM ASCII date once, so the whole log stays readable as UTF-8 (cmd's %date% emits
REM a GBK weekday, which is what made the old log unreadable in any one encoding).
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set "TODAY=%%i"
if not defined TODAY set "TODAY=unknown-date"

call :stamp
echo [!TS!] === auto_run start force=!FORCE! === >> "%LOG%"

REM ---------- 1. stale / live lock -------------------------------------------
if not exist "%LOCK%" goto lock_ok
for /f %%a in ('powershell -NoProfile -Command "[int]((Get-Date)-(Get-Item '%LOCK%').LastWriteTime).TotalMinutes"') do set "LOCKAGE=%%a"
if not defined LOCKAGE set "LOCKAGE=999"
if !LOCKAGE! LSS 10 (
    call :stamp
    echo [!TS!] another run appears active, lock age !LOCKAGE!m -- skip >> "%LOG%"
    exit /b 0
)
call :stamp
echo [!TS!] previous run was INTERRUPTED, stale lock age !LOCKAGE!m >> "%LOG%"
del "%LOCK%" >nul 2>&1
set "PREV_INTERRUPTED=1"

:lock_ok
REM ---------- 2. idempotency gate --------------------------------------------
if "!FORCE!"=="1" goto proceed
python main.py --check-fresh >> "%LOG%" 2>&1
if not "!errorlevel!"=="0" goto proceed

call :stamp
echo [!TS!] this week already has a valid snapshot -- report only, no crawl >> "%LOG%"
if "!PREV_INTERRUPTED!"=="1" echo INTERRUPTED !TS! run was killed, but this week's data is intact >> "%CRASH%"
python main.py --report >> "%LOG%" 2>&1
if not "!errorlevel!"=="0" exit /b 2
exit /b 0

:proceed
REM ---------- 3. rotate log by rename when large ------------------------------
REM Renaming is byte-for-byte; the old Get-Content|Set-Content pipeline read and
REM wrote the same file, so it never actually trimmed anything.
for %%A in ("%LOG%") do if %%~zA GTR 524288 move /y "%LOG%" "%LOG%.1" >nul 2>&1

if "!PREV_INTERRUPTED!"=="1" echo INTERRUPTED !TS! run was killed mid-crawl and left a stale lock >> "%CRASH%"

REM ---------- 4. proxy wait + crawl, up to MAX_ATTEMPTS -----------------------
:attempt
set "PROXY_MAX=36"
if !ATTEMPT! GTR 0 set "PROXY_MAX=6"
set "RETRY=0"
call :stamp
echo [!TS!] waiting for proxy, attempt !ATTEMPT!/!MAX_ATTEMPTS! >> "%LOG%"
if !ATTEMPT! GTR 0 goto check_proxy
ping -n 30 127.0.0.1 >nul

:check_proxy
powershell -NoProfile -Command "(New-Object Net.Sockets.TcpClient).Connect('127.0.0.1',7897)" >nul 2>&1
if !errorlevel!==0 (
    set "HTTP_PROXY=http://127.0.0.1:7897"
    set "HTTPS_PROXY=http://127.0.0.1:7897"
    set "HTTP_PROXY_BACKUP=http://127.0.0.1:7993"
    goto proxy_ok
)
powershell -NoProfile -Command "(New-Object Net.Sockets.TcpClient).Connect('127.0.0.1',7993)" >nul 2>&1
if !errorlevel!==0 (
    set "HTTP_PROXY=http://127.0.0.1:7993"
    set "HTTPS_PROXY=http://127.0.0.1:7993"
    set "HTTP_PROXY_BACKUP=http://127.0.0.1:7897"
    goto proxy_ok
)

set /a RETRY+=1
if !RETRY! GEQ !PROXY_MAX! goto proxy_fail
if !RETRY! LEQ 6 goto retry_30s
call :stamp
echo [!TS!] proxy not ready, retry in 5min !RETRY!/!PROXY_MAX! >> "%LOG%"
if !RETRY!==7 call :warn_balloon
ping -n 300 127.0.0.1 >nul
goto check_proxy

:retry_30s
call :stamp
echo [!TS!] proxy not ready, retry in 30s !RETRY!/!PROXY_MAX! >> "%LOG%"
ping -n 30 127.0.0.1 >nul
goto check_proxy

:proxy_ok
call :stamp
echo [!TS!] proxy ready, starting crawl attempt !ATTEMPT!/!MAX_ATTEMPTS! >> "%LOG%"
echo RUNNING !TS! attempt=!ATTEMPT! > "%LOCK%"

python main.py --save >> "%LOG%" 2>&1
set "RC=!errorlevel!"
if not "!RC!"=="0" goto crawl_failed

call :stamp
echo [!TS!] crawl ok, building report >> "%LOG%"
python main.py --report >> "%LOG%" 2>&1
set "RC=!errorlevel!"
if not "!RC!"=="0" goto crawl_failed

call :stamp
echo [!TS!] DONE rc=0 >> "%LOG%"
del "%LOCK%" >nul 2>&1
exit /b 0

:crawl_failed
call :stamp
echo [!TS!] FAILED rc=!RC! attempt !ATTEMPT!/!MAX_ATTEMPTS! >> "%LOG%"
set /a ATTEMPT+=1
if !ATTEMPT! GEQ !MAX_ATTEMPTS! goto give_up
call :stamp
echo [!TS!] retrying in 60s >> "%LOG%"
ping -n 60 127.0.0.1 >nul
goto attempt

:give_up
call :stamp
echo CRAWL-FAILED !TS! rc=!RC! attempts=!MAX_ATTEMPTS! >> "%CRASH%"
del "%LOCK%" >nul 2>&1
exit /b !RC!

:proxy_fail
call :stamp
echo [!TS!] proxy dead after !PROXY_MAX! tries, giving up >> "%LOG%"
echo PROXY-DEAD !TS! >> "%CRASH%"
del "%LOCK%" >nul 2>&1
exit /b 1

REM ---------- helpers --------------------------------------------------------
:stamp
set "TS=!TODAY! !TIME:~0,8!"
exit /b 0

:warn_balloon
powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $n = New-Object System.Windows.Forms.NotifyIcon; $n.Icon = [System.Drawing.SystemIcons]::Warning; $n.BalloonTipTitle = 'GitHub-Trends crawler'; $n.BalloonTipText = 'Proxy 7897 and 7993 both unreachable. Check Clash.'; $n.Visible = $true; $n.ShowBalloonTip(15000)" >nul 2>&1
exit /b 0
