@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo   正在启动「选股工作台」+ 手机隧道,请稍候约10秒...
echo ============================================================
start "选股App引擎(别关)" /min ".venv\Scripts\python.exe" -m streamlit run app.py --server.port 8501 --server.headless true
timeout /t 9 >nul
echo.
echo ############################################################
echo #  手机浏览器打开下面这个 https 网址 (密码: lei2026)
echo #  每次启动网址会变,以本窗口显示的为准
echo #  用完直接关掉这个窗口即可停止
echo ############################################################
echo.
"C:\Users\xiaoy\AppData\Local\Microsoft\WinGet\Packages\Cloudflare.cloudflared_Microsoft.Winget.Source_8wekyb3d8bbwe\cloudflared.exe" tunnel --url http://localhost:8501
