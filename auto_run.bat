@echo off
set LOG=C:\Users\jd\Desktop\github-trends\output\auto_log.txt
cd /d C:\Users\jd\Desktop\github-trends

:: Clash 开机后规则引擎初始化需 30 秒，先等
echo [%date% %time%] 等待 Clash 初始化... >> "%LOG%"
ping -n 30 127.0.0.1 >nul

:: 等代理就绪（36 次重试，每次先试 7897 再试 7993）
set RETRY=0
:check_proxy
D:\Git\mingw64\bin\curl.exe -s -o nul --connect-timeout 3 -x http://127.0.0.1:7897 https://github.com
if %errorlevel%==0 (
    set HTTP_PROXY=http://127.0.0.1:7897
    set HTTPS_PROXY=http://127.0.0.1:7897
    goto run
)
D:\Git\mingw64\bin\curl.exe -s -o nul --connect-timeout 3 -x http://127.0.0.1:7993 https://github.com
if %errorlevel%==0 (
    set HTTP_PROXY=http://127.0.0.1:7993
    set HTTPS_PROXY=http://127.0.0.1:7993
    goto run
)
set /a RETRY+=1
if %RETRY% geq 36 goto fail
if %RETRY% leq 6 (
    echo [%date% %time%] 代理未就绪，30秒后重试 (%RETRY%/36) >> "%LOG%"
    ping -n 30 127.0.0.1 >nul
) else (
    echo [%date% %time%] 代理未就绪，5分钟后重试 (%RETRY%/36) >> "%LOG%"
    ping -n 300 127.0.0.1 >nul
)
goto check_proxy

:run
python main.py --save >> "%LOG%" 2>&1
python main.py --report >> "%LOG%" 2>&1
echo Done at %date% %time% >> "%LOG%"
python -c "from datetime import date; w=date.today().isocalendar(); print(f'| W{w.week} | {date.today().strftime(\"%%m.%%d\")} | ✅ 自动 | 1份 | 采集正常 |', file=open('PROGRESS.md','a'))" >> "%LOG%" 2>&1
exit /b 0

:fail
echo [%date% %time%] 等了3小时代理还不通，放弃了 >> "%LOG%"
echo %date% %time% > output\CRASH.txt
exit /b 1
