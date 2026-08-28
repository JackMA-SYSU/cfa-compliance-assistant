@echo off
chcp 65001 >nul
cd /d D:\cfa-compliance-assistant
echo 正在启动 CFA 合规自检助手（局域网演示模式）...
echo 关闭本窗口即可停止服务。
echo.
echo [自动清理] 关闭占用 8000 端口的旧进程...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)
timeout /t 1 /nobreak >nul
python scripts\start_demo.py
pause
