@echo off
chcp 65001 >nul
cd /d D:\cfa-compliance-assistant
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)
timeout /t 1 /nobreak >nul
python scripts\start_demo.py
pause
