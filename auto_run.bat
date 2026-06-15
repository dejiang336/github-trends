@echo off
set HTTP_PROXY=http://127.0.0.1:7897
set HTTPS_PROXY=http://127.0.0.1:7897
set LOG=C:\Users\jd\Desktop\github-trends\output\auto_log.txt
cd /d C:\Users\jd\Desktop\github-trends

:: 等代理就绪（最多 36 次 × 5 分钟 = 3 小时）
set RETRY=0
:check_proxy
C:\Windows\System32\curl.exe -s -o nul --connect-timeout 3 -x http://127.0.0.1:7897 https://github.com
if %errorlevel%==0 goto run
set /a RETRY+=1
if %RETRY% geq 36 goto fail
echo [%date% %time%] 代理未就绪，5分钟后重试 (%RETRY%/36) >> "%LOG%"
ping -n 300 127.0.0.1 >nul
goto check_proxy

:run
python main.py --save >> "%LOG%" 2>&1
python main.py --report >> "%LOG%" 2>&1
echo Done at %date% %time% >> "%LOG%"
exit /b 0

:fail
echo [%date% %time%] 等了3小时代理还不通，放弃了 >> "%LOG%"
exit /b 1
