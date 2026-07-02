@echo off
set LOG=C:\Users\jd\Desktop\github-trends\output\auto_log.txt
cd /d C:\Users\jd\Desktop\github-trends

:: 日志旋转：保留最近 300 行
if exist "%LOG%" (
    powershell -Command "Get-Content '%LOG%' -Tail 300 | Set-Content '%LOG%'" >nul 2>&1
)

:: Wait 30s for proxy init
echo [%date% %time%] Waiting for proxy... >> "%LOG%"
ping -n 30 127.0.0.1 >nul

:: Retry loop: 36 tries (first 6 every 30s, rest every 5min = max ~2.5h)
set RETRY=0
:check_proxy
curl -s -o nul --connect-timeout 3 -x http://127.0.0.1:7897 https://github.com
if %errorlevel%==0 (
    set HTTP_PROXY=http://127.0.0.1:7897
    set HTTPS_PROXY=http://127.0.0.1:7897
    goto run
)
curl -s -o nul --connect-timeout 3 -x http://127.0.0.1:7993 https://github.com
if %errorlevel%==0 (
    set HTTP_PROXY=http://127.0.0.1:7993
    set HTTPS_PROXY=http://127.0.0.1:7993
    goto run
)
set /a RETRY+=1
if %RETRY% geq 36 goto fail
if %RETRY% leq 6 (
    echo [%date% %time%] Proxy not ready, retry in 30s (%RETRY%/36) >> "%LOG%"
    ping -n 30 127.0.0.1 >nul
) else (
    echo [%date% %time%] Proxy not ready, retry in 5min (%RETRY%/36) >> "%LOG%"
    ping -n 300 127.0.0.1 >nul
)
goto check_proxy

:run
python main.py --save >> "%LOG%" 2>&1
python main.py --report >> "%LOG%" 2>&1
echo Done at %date% %time% >> "%LOG%"
python -c "from datetime import date; w=date.today().isocalendar(); print(f'    | W{w.week} | {date.today().strftime(\"%%m.%%d\")} | ✅ auto | 1 file | OK |', file=open('PROGRESS.md','a'))" >> "%LOG%" 2>&1
exit /b 0

:fail
echo [%date% %time%] Proxy dead after 3h, giving up >> "%LOG%"
echo %date% %time% > output\CRASH.txt
exit /b 1
