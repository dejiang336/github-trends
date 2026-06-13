@echo off
set HTTP_PROXY=http://127.0.0.1:7897
set HTTPS_PROXY=http://127.0.0.1:7897
cd /d C:\Users\jd\Desktop\github-trends

:: 等代理就绪（最多等 12 次 × 5 分钟 = 1 小时）
set RETRY=0
:check_proxy
curl -s -o nul --connect-timeout 3 -x http://127.0.0.1:7897 https://github.com
if %errorlevel%==0 goto run
set /a RETRY+=1
if %RETRY% geq 12 goto fail
echo [%date% %time%] 代理未就绪，5分钟后重试 (%RETRY%/12) >> output\auto_log.txt
timeout /t 300 /nobreak >nul
goto check_proxy

:run
python main.py --save >> output\auto_log.txt 2>&1
python main.py --report >> output\auto_log.txt 2>&1
echo Done at %date% %time% >> output\auto_log.txt
exit /b 0

:fail
echo [%date% %time%] 等了1小时代理还不通，放弃了 >> output\auto_log.txt
exit /b 1
