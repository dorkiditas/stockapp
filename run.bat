@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 启动选股工作台... 浏览器会自动打开 http://localhost:8501
".venv\Scripts\python.exe" -m streamlit run app.py
pause
